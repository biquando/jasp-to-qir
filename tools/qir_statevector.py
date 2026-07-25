#!/usr/bin/env python3
"""Run textual QIR with Selene/QuEST and emit its state vector as JSON.

The utility lowers QIR to Quantinuum QIS, instruments the lowered entry point
in a temporary copy, executes one ideal QuEST shot with Selene, extracts the
resulting state dump, and writes the same ``jasp-to-qir-statevector-v1`` JSON format as
``qrisp_statevector.py``. The input QIR and the conversion pipeline are not
modified.

Install Selene separately before use:

    uv pip install --python ./venv/bin/python selene-sim

Examples:

    ./venv/bin/python tools/qir_statevector.py program.ll
    ./venv/bin/python tools/qir_statevector.py program.ll -o program.state.json
    ./venv/bin/python tools/qir_statevector.py dynamic.ll --n-qubits 5

For static QIR, ``required_num_qubits`` is read from the entry-point
attributes. Dynamic-allocation QIR must supply the simulator capacity with
``--n-qubits``. Use ``--entry-point`` only when automatic entry-point attribute
detection is insufficient.

By default, the dump is inserted immediately before every return in the entry
point. ``--at before-first-measurement`` instead captures the state just before
the first textual ``mz`` call; this is useful for comparing state-preparation
programs whose normal entry point ends by measuring its outputs. It is not a
general representation of adaptive programs with multiple stochastic paths.

The dense ``amplitudes`` array uses qubit 0 as the leftmost (most-significant)
bit. Selene's ordered-qubit state extraction converts QuEST's internal
least-significant-qubit convention. The first nonzero amplitude is made real
and nonnegative to remove physically irrelevant global phase.

Only textual LLVM IR (``.ll``) is accepted because adding the state-dump call
requires instrumentation. Selene itself also accepts bitcode, but this utility
does not rewrite bitcode.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile


FORMAT = "jasp-to-qir-statevector-v1"
TAG = "statevector"
DUMP_TAG = f"USER:STATE:{TAG}"
PREFIX = "__jasp-to-qir_statevector"


def entry_attribute_groups(source: str) -> set[str]:
    groups = set()
    pattern = re.compile(r'^\s*attributes\s+#(\d+)\s*=\s*\{([^}]*)\}', re.MULTILINE)
    for match in pattern.finditer(source):
        if '"entry_point"' in match.group(2):
            groups.add(match.group(1))
    return groups


def find_entry(source: str, requested: str | None) -> tuple[list[str], int, int, str]:
    lines = source.splitlines(keepends=True)
    groups = entry_attribute_groups(source)
    definitions = []
    definition = re.compile(r'^\s*define\b.*?@(?:"([^"]+)"|([-A-Za-z$._0-9]+))\s*\(')
    for index, line in enumerate(lines):
        match = definition.search(line)
        if not match:
            continue
        name = match.group(1) or match.group(2)
        group = re.search(r'#(\d+)\s*\{\s*(?:;.*)?$', line)
        is_entry = '"entry_point"' in line or (
            group is not None and group.group(1) in groups
        )
        definitions.append((index, name, is_entry))

    if requested is not None:
        candidates = [item for item in definitions if item[1] == requested]
        if not candidates:
            raise ValueError(f"entry-point function {requested!r} was not found")
    else:
        candidates = [item for item in definitions if item[2]]
        if not candidates:
            raise ValueError(
                "no function with the QIR entry_point attribute was found; "
                "use --entry-point"
            )
        if len(candidates) > 1:
            names = ", ".join(item[1] for item in candidates)
            raise ValueError(f"multiple QIR entry points found ({names}); use --entry-point")

    start, name, _ = candidates[0]
    depth = 0
    opened = False
    end = None
    for index in range(start, len(lines)):
        depth += lines[index].count("{") - lines[index].count("}")
        opened = opened or "{" in lines[index]
        if opened and depth == 0:
            end = index
            break
    if end is None:
        raise ValueError(f"could not find the end of entry-point function {name!r}")
    return lines, start, end, name


def state_dump_ir(n_qubits: int, needs_declaration: bool) -> str:
    qubits = ", ".join(f"i64 {index}" for index in range(n_qubits))
    declaration = "declare void @print_state_result(ptr, i64, ptr)\n" if needs_declaration else ""
    return (
        f'@{PREFIX}_tag = private constant [{len(DUMP_TAG) + 1} x i8] '
        f'c"\\{len(DUMP_TAG):02X}{DUMP_TAG}"\n'
        f"@{PREFIX}_qubits = private constant [{n_qubits} x i64] [{qubits}]\n"
        f"@{PREFIX}_mask = private constant [{n_qubits} x i1] zeroinitializer\n"
        f"@{PREFIX}_array = private constant <{{ i32, i32, ptr, ptr }}> "
        f"<{{ i32 {n_qubits}, i32 1, ptr @{PREFIX}_qubits, ptr @{PREFIX}_mask }}>\n"
        f"{declaration}\n"
    )


def instrument_qis(source: str, n_qubits: int, at: str) -> str:
    """Add a Base QIS state-result call after QIR has been lowered to QIS."""
    if f"@{PREFIX}_" in source:
        raise ValueError(f"input already defines a reserved @{PREFIX}_ symbol")
    lines = source.splitlines(keepends=True)
    definition = re.compile(r"^\s*define\b.*@___user_qir_main\s*\(")
    starts = [index for index, line in enumerate(lines) if definition.search(line)]
    if len(starts) != 1:
        raise ValueError("lowered QIS does not contain exactly one ___user_qir_main")
    start = starts[0]
    depth = 0
    end = None
    for index in range(start, len(lines)):
        depth += lines[index].count("{") - lines[index].count("}")
        if index > start and depth == 0:
            end = index
            break
    if end is None:
        raise ValueError("could not find the end of lowered QIS entry point")
    call = (
        f"  call void @print_state_result(ptr @{PREFIX}_tag, i64 {len(DUMP_TAG)}, "
        f"ptr @{PREFIX}_array)\n"
    )
    points: list[int]
    if at == "return":
        points = [
            index
            for index in range(start + 1, end)
            if re.match(r"^\s*ret\b", lines[index])
        ]
        if not points:
            raise ValueError("lowered QIS entry point contains no return instruction")
    else:
        measurement = re.compile(r"\bcall\b.*@___lazy_measure(?:_leaked)?\s*\(")
        points = [
            index
            for index in range(start + 1, end)
            if measurement.search(lines[index])
        ][:1]
        if not points:
            raise ValueError("lowered QIS entry point contains no measurement")

    for index in reversed(points):
        lines.insert(index, call)
    globals_ir = state_dump_ir(
        n_qubits, not bool(re.search(r"\bdeclare\b.*@print_state_result\s*\(", source))
    )
    lines.insert(start, globals_ir)
    return "".join(lines)


def lower_qir_to_qis(source: str) -> str:
    try:
        from llvmlite import binding
        from qir_qis import qir_ll_to_bc, qir_to_qis
    except ImportError as exc:
        raise RuntimeError(
            "Selene and qir-qis are not installed; run: "
            "uv pip install --python ./venv/bin/python selene-sim"
        ) from exc

    machine = platform.machine().lower()
    target = "aarch64" if machine in {"arm64", "aarch64"} else "x86-64"
    lowered_bitcode = qir_to_qis(qir_ll_to_bc(source), opt_level=0, target=target)
    return str(binding.parse_bitcode(lowered_bitcode))


def required_qubits(source: str) -> int | None:
    values = {
        int(value)
        for value in re.findall(r'"required_num_qubits"\s*=\s*"(\d+)"', source)
    }
    if not values:
        return None
    if len(values) != 1:
        raise ValueError("QIR contains conflicting required_num_qubits values")
    return values.pop()


def canonicalize_global_phase(state, threshold: float):
    import numpy as np

    vector = np.asarray(state, dtype=np.complex128).reshape(-1).copy()
    norm = float(np.linalg.norm(vector))
    if norm == 0:
        raise ValueError("simulator returned a zero state vector")
    vector /= norm
    nonzero = np.flatnonzero(np.abs(vector) > threshold)
    if nonzero.size:
        phase = vector[nonzero[0]] / abs(vector[nonzero[0]])
        vector /= phase
    vector.real[np.abs(vector.real) < threshold] = 0.0
    vector.imag[np.abs(vector.imag) < threshold] = 0.0
    return vector


def write_document(state, source: Path, entry: str, threshold: float, output: Path | None):
    vector = canonicalize_global_phase(state, threshold)
    size = len(vector)
    n_qubits = size.bit_length() - 1
    if size != 1 << n_qubits:
        raise ValueError(f"state-vector length {size} is not a power of two")
    document = {
        "format": FORMAT,
        "source": {"kind": "qir-selene-quest", "path": str(source.resolve())},
        "entry_point": entry,
        "num_qubits": n_qubits,
        "qubits": [f"q{index}" for index in range(n_qubits)],
        "basis_order": "qubit 0 is the leftmost (most-significant) bit",
        "global_phase": "first nonzero amplitude is real and nonnegative",
        "amplitudes": [[float(value.real), float(value.imag)] for value in vector],
    }
    encoded = json.dumps(document, indent=2, sort_keys=False) + "\n"
    if output is None:
        sys.stdout.write(encoded)
    else:
        output.write_text(encoded, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", type=Path, help="textual QIR LLVM IR (.ll)")
    parser.add_argument("--n-qubits", type=int, help="Selene simulator qubit capacity")
    parser.add_argument("--entry-point", help="QIR entry-point function name")
    parser.add_argument(
        "--at",
        choices=("return", "before-first-measurement"),
        default="return",
        help="where to capture the state (default: return)",
    )
    parser.add_argument("--seed", type=int, help="QuEST random seed")
    parser.add_argument("-o", "--output", type=Path, help="write JSON to this file")
    parser.add_argument(
        "--zero-threshold",
        type=float,
        default=1e-12,
        help="zero amplitudes smaller than this magnitude (default: 1e-12)",
    )
    args = parser.parse_args()

    try:
        if not args.program.is_file():
            raise ValueError(f"program does not exist: {args.program}")
        if args.program.suffix.lower() != ".ll":
            raise ValueError("input must be textual LLVM IR with a .ll extension")
        if not math.isfinite(args.zero_threshold) or args.zero_threshold < 0:
            raise ValueError("--zero-threshold must be a finite nonnegative number")
        source = args.program.read_text(encoding="utf-8")
        n_qubits = (
            args.n_qubits if args.n_qubits is not None else required_qubits(source)
        )
        if n_qubits is None:
            raise ValueError(
                "qubit capacity is not present in QIR; pass --n-qubits for dynamic QIR"
            )
        if n_qubits <= 0:
            raise ValueError("--n-qubits must be positive")
        _, _, _, entry_name = find_entry(source, args.entry_point)
        lowered = lower_qir_to_qis(source)
        instrumented = instrument_qis(lowered, n_qubits, args.at)
        try:
            from selene_sim import Quest, build
        except ImportError as exc:
            raise RuntimeError(
                "Selene is not installed; run: ./venv/bin/pip install selene-sim"
            ) from exc

        with tempfile.TemporaryDirectory(prefix="jasp-to-qir-qir-statevector-") as directory:
            temporary = Path(directory)
            instrumented_path = temporary / "instrumented.ll"
            instrumented_path.write_text(instrumented, encoding="utf-8")
            clang = shutil.which("clang")
            if clang is None:
                raise RuntimeError("clang is required to compile instrumented QIR")
            target = subprocess.run(
                [clang, "-dumpmachine"], text=True, capture_output=True, check=True
            ).stdout.strip()
            object_path = temporary / "instrumented.o"
            compilation = subprocess.run(
                [
                    clang,
                    "-target",
                    target,
                    "-Wno-override-module",
                    "-c",
                    instrumented_path,
                    "-o",
                    object_path,
                ],
                text=True,
                capture_output=True,
            )
            if compilation.returncode:
                diagnostic = compilation.stderr.strip() or compilation.stdout.strip()
                raise RuntimeError(f"failed to compile instrumented QIR: {diagnostic}")
            cache_key = "ZIG_GLOBAL_CACHE_DIR"
            previous_cache = os.environ.get(cache_key)
            os.environ[cache_key] = str(temporary / "zig-global-cache")
            try:
                runner = build(object_path, build_dir=temporary / "build")
            finally:
                if previous_cache is None:
                    os.environ.pop(cache_key, None)
                else:
                    os.environ[cache_key] = previous_cache
            plugin = Quest(random_seed=args.seed)
            results = runner.run(simulator=plugin, n_qubits=n_qubits)
            states = plugin.extract_states_dict(results)
            if TAG not in states:
                raise RuntimeError("Selene execution did not return the requested state dump")
            state = states[TAG].get_single_state(args.zero_threshold)
            write_document(
                state, args.program, entry_name, args.zero_threshold, args.output
            )
    except Exception as exc:
        parser.exit(1, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
