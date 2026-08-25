#!/usr/bin/env python3
"""Lower Jasp MLIR through to Adaptive-Profile QIR."""

import argparse
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JASP_OPT = ROOT / "build/jasp-to-qir"
LLVM_BIN = os.environ.get("LLVM_BIN")
MLIR_TRANSLATE = Path(LLVM_BIN) / "mlir-translate" if LLVM_BIN else "mlir-translate"


@dataclass(frozen=True)
class QirProfile:
    resource_management: str
    ir_functions: bool
    backwards_branching: bool
    multiple_target_branching: bool
    multiple_return_points: bool
    float_computations: bool


def run(*args: str | Path) -> None:
    command = [str(arg) for arg in args]
    try:
        subprocess.run(command, check=True, cwd=ROOT)
    except FileNotFoundError as error:
        raise ValueError(f"required tool not found: {command[0]}") from error


def read_profile(mlir: str) -> QirProfile:
    """Read metadata produced by the Jasp lowering pass."""

    # Find the MLIR module attributes
    match = re.search(r"module @\w+ attributes {(.*)}", mlir)
    if not match:
        raise ValueError(f"lowering did not output MLIR module attributes")
    attributes = match.group(1)

    # Determine static or dynamic resource management mode
    mode_match = re.search(
        r'metadata\.resource_management\s*=\s*"(static|dynamic)"', attributes
    )
    if not mode_match:
        raise ValueError("lowering did not report resource_management")
    resource_management = mode_match.group(1)

    # Parse other (boolean) flags
    def module_flag(name: str) -> bool:
        match = re.search(rf"module_flag\.{name}\s*=\s*(true|false)", attributes)
        if not match:
            raise ValueError(f"lowering did not report {name}")
        return match.group(1) == "true"

    return QirProfile(
        resource_management=resource_management,
        ir_functions=module_flag("ir_functions"),
        backwards_branching=module_flag("backwards_branching"),
        multiple_target_branching=module_flag("multiple_target_branching"),
        multiple_return_points=module_flag("multiple_return_points"),
        float_computations=module_flag("float_computations"),
    )


def set_qir_module_flags(profile: QirProfile, llvm_ir: str) -> str:
    # Remove translator-added module flags before adding QIR's flags
    body = "\n".join(line for line in llvm_ir.splitlines() if not line.startswith("!"))

    # Add QIR module flags
    dynamic = str(profile.resource_management == "dynamic").lower()
    return f"""{body}

!llvm.module.flags = !{{!0, !1, !2, !3, !4, !5, !6, !7, !8, !9, !10}}
!0 = !{{i32 1, !"qir_major_version", i32 2}}
!1 = !{{i32 7, !"qir_minor_version", i32 1}}
!2 = !{{i32 1, !"dynamic_qubit_management", i1 {dynamic}}}
!3 = !{{i32 1, !"dynamic_result_management", i1 {dynamic}}}
!4 = !{{i32 1, !"ir_functions", i1 {str(profile.ir_functions).lower()}}}
!5 = !{{i32 1, !"backwards_branching", i2 {3 if profile.backwards_branching else 0}}}
!6 = !{{i32 1, !"multiple_target_branching", i1 {str(profile.multiple_target_branching).lower()}}}
!7 = !{{i32 1, !"multiple_return_points", i1 {str(profile.multiple_return_points).lower()}}}
!8 = !{{i32 1, !"arrays", i1 {dynamic}}}
!9 = !{{i32 5, !"int_computations", !11}}
!10 = !{{i32 5, !"float_computations", !12}}
!11 = !{{!"i64"}}
!12 = !{{{'!"double"' if profile.float_computations else ""}}}
"""


def convert(
    input_path: Path,
    output_path: Path,
    keep_intermediates: bool = False,
    resource_management: str = "static",
) -> None:
    stem = output_path.with_suffix("")
    llvm_mlir = stem.with_suffix(".llvm.mlir")
    raw_llvm = stem.with_suffix(".raw.ll")

    intermediates = (llvm_mlir, raw_llvm)
    try:
        run(
            JASP_OPT,
            input_path,
            f"--lower-jasp-to-qir=resource-management={resource_management}",
            "--canonicalize",
            "--convert-scf-to-cf",
            "--convert-cf-to-llvm",
            "--convert-arith-to-llvm",
            "--convert-func-to-llvm",
            "--reconcile-unrealized-casts",
            "--finalize-qir-llvm",
            "-o",
            llvm_mlir,
        )
        profile = read_profile(llvm_mlir.read_text(encoding="utf-8"))

        run(MLIR_TRANSLATE, "--mlir-to-llvmir", llvm_mlir, "-o", raw_llvm)
        output_path.write_text(
            set_qir_module_flags(profile, raw_llvm.read_text())
        )
    finally:
        if not keep_intermediates:
            for path in intermediates:
                path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--keep-intermediates",
        action="store_true",
        help="retain generated .mlir and .raw.ll files",
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="use dynamic runtime qubit/result allocation and arrays",
    )
    args = parser.parse_args()

    try:
        convert(
            args.input,
            args.output,
            args.keep_intermediates,
            "dynamic" if args.dynamic else "static",
        )

    except ValueError as error:
        parser.exit(1, f"error: {error}\n")
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from None


if __name__ == "__main__":
    main()
