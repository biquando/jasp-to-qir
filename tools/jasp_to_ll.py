#!/usr/bin/env python3
"""Lower Jasp MLIR through SCF, CF, and LLVM to Adaptive-Profile QIR."""

import argparse
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JASP_OPT = ROOT / "build/jasp-to-qir"
LLVM_BIN = Path(os.environ.get("LLVM_BIN", "/opt/homebrew/opt/llvm/bin"))
MLIR_TRANSLATE = LLVM_BIN / "mlir-translate"


@dataclass(frozen=True)
class QirProfile:
    qubits: int
    results: int
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
    """Read facts produced by the Jasp lowering pass."""

    def integer(name: str) -> int:
        match = re.search(rf"jasp\.{name}\s*=\s*(\d+)\s*:\s*i64", mlir)
        if not match:
            raise ValueError(f"lowering did not report {name}")
        return int(match.group(1))

    def boolean(name: str) -> bool:
        match = re.search(rf"jasp\.{name}\s*=\s*(true|false)", mlir)
        if not match:
            raise ValueError(f"lowering did not report {name}")
        return match.group(1) == "true"

    return QirProfile(
        qubits=integer("required_num_qubits"),
        results=integer("required_num_results"),
        ir_functions=boolean("ir_functions"),
        backwards_branching=boolean("backwards_branching"),
        multiple_target_branching=boolean("multiple_target_branching"),
        multiple_return_points=boolean("multiple_return_points"),
        float_computations=boolean("float_computations"),
    )


def pointer(index: int) -> str:
    if index == 0:
        return "null"
    return f"nonnull inttoptr (i64 {index} to ptr)"


def instrument_main(llvm_ir: str) -> str:
    """Add QIR initialization and attributes to the entry point."""
    lines = llvm_ir.splitlines()
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"define i64 @main\(\)", line)
        ),
        None,
    )
    if start is None:
        raise ValueError("could not find the @main entry point")
    lines[start] = lines[start].replace(" {", " #0 {")
    initialize_at = start + 1
    if lines[initialize_at].strip().endswith(":"):
        initialize_at += 1
    lines.insert(initialize_at, "  call void @__quantum__rt__initialize(ptr null)")

    depth = 0
    returns: list[int] = []
    for index in range(start, len(lines)):
        depth += lines[index].count("{") - lines[index].count("}")
        if depth and lines[index].strip().startswith("ret i64"):
            returns.append(index)
        if index > start and depth == 0:
            break
    if not returns:
        raise ValueError("could not find the @main return")

    return "\n".join(lines) + "\n"


MEASUREMENT_CALL = re.compile(
    r"@__quantum__qis__mz__body\(.*?,\s*ptr\s+"
    r"(?P<pointer>null|(?:nonnull\s+)?inttoptr\s*\(i64\s+(?P<id>\d+)\s+to\s+ptr\))\)"
)


def record_measurements(llvm_ir: str) -> str:
    """Record each result immediately after the measurement that writes it."""
    lines: list[str] = []
    for line in llvm_ir.splitlines():
        lines.append(line)
        match = MEASUREMENT_CALL.search(line)
        if not match:
            continue

        resource = int(match.group("id") or 0)
        indent = line[: len(line) - len(line.lstrip())]
        lines.append(
            f"{indent}call void @__quantum__rt__result_record_output"
            f"(ptr {pointer(resource)}, ptr @label{resource})"
        )
    return "\n".join(lines) + "\n"


def module_flags(profile: QirProfile) -> str:
    integer_types = '!{!"i64"}'
    float_types = '!{!"double"}' if profile.float_computations else "!{}"
    return f"""!llvm.module.flags = !{{!0, !1, !2, !3, !4, !5, !6, !7, !8, !9, !10}}
!0 = !{{i32 1, !"qir_major_version", i32 2}}
!1 = !{{i32 7, !"qir_minor_version", i32 0}}
!2 = !{{i32 1, !"dynamic_qubit_management", i1 false}}
!3 = !{{i32 1, !"dynamic_result_management", i1 false}}
!4 = !{{i32 1, !"ir_functions", i1 {str(profile.ir_functions).lower()}}}
!5 = !{{i32 1, !"backwards_branching", i2 {1 if profile.backwards_branching else 0}}}
!6 = !{{i32 1, !"multiple_target_branching", i1 {str(profile.multiple_target_branching).lower()}}}
!7 = !{{i32 1, !"multiple_return_points", i1 {str(profile.multiple_return_points).lower()}}}
!8 = !{{i32 1, !"arrays", i1 false}}
!9 = !{{i32 5, !"int_computations", !11}}
!10 = !{{i32 5, !"float_computations", !12}}
!11 = {integer_types}
!12 = {float_types}
"""


def strip_translation_boilerplate(llvm_ir: str) -> str:
    return "\n".join(
        line
        for line in llvm_ir.splitlines()
        if not line.startswith(
            (
                "; ModuleID",
                "source_filename",
                "!",
                "declare void @__quantum__qis__mz__body",
                "declare void @__quantum__qis__reset__body",
                "declare i1 @__quantum__rt__read_result",
                "declare void @__quantum__rt__result_record_output",
                "declare void @__quantum__rt__initialize",
            )
        )
    )


def finalize_qir(profile: QirProfile, llvm_ir: str) -> str:
    labels = "\n".join(
        f'@label{index} = internal constant [{len(f"bit_{index}") + 1} x i8] '
        f'c"bit_{index}\\00"'
        for index in range(profile.results)
    )
    body = instrument_main(record_measurements(strip_translation_boilerplate(llvm_ir)))
    return f"""; QIR 2.1 Adaptive Profile
%Qubit = type opaque
%Result = type opaque

{labels}

{body}
declare void @__quantum__qis__mz__body(ptr, ptr writeonly) #1
declare void @__quantum__qis__reset__body(ptr) #1
declare void @__quantum__rt__initialize(ptr)
declare i1 @__quantum__rt__read_result(ptr readonly)
declare void @__quantum__rt__result_record_output(ptr, ptr)

attributes #0 = {{ "entry_point" "qir_profiles"="adaptive_profile" "output_labeling_schema"="schema_id" "required_num_qubits"="{profile.qubits}" "required_num_results"="{profile.results}" }}
attributes #1 = {{ "irreversible" }}

{module_flags(profile)}"""


def convert(input_path: Path, output_path: Path, keep_intermediates: bool = False) -> None:
    stem = output_path.with_suffix("")
    llvm = stem.with_suffix(".llvm.mlir")
    raw_llvm = stem.with_suffix(".raw.ll")

    intermediates = (llvm, raw_llvm)
    try:
        run(
            JASP_OPT,
            input_path,
            "--lower-jasp-to-qir",
            "--canonicalize",
            "--convert-scf-to-cf",
            "--convert-cf-to-llvm",
            "--convert-arith-to-llvm",
            "--convert-func-to-llvm",
            "--reconcile-unrealized-casts",
            "-o",
            llvm,
        )
        profile = read_profile(llvm.read_text(encoding="utf-8"))
        run(MLIR_TRANSLATE, "--mlir-to-llvmir", llvm, "-o", raw_llvm)

        raw = raw_llvm.read_text(encoding="utf-8")
        output_path.write_text(finalize_qir(profile, raw), encoding="utf-8")
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
    args = parser.parse_args()
    try:
        convert(args.input, args.output, args.keep_intermediates)
    except ValueError as error:
        parser.exit(1, f"error: {error}\n")
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from None


if __name__ == "__main__":
    main()
