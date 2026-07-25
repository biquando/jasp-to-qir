#!/usr/bin/env python3
"""Emit the state vector prepared by a Qrisp Python program as JSON.

The input file must define a zero-argument ``prepare_state`` function (or a
function selected with ``--function``). The function should build an unmeasured
Qrisp program and return a ``QuantumSession``, a quantum value with a ``.qs``
session, or a nested collection containing quantum values from one session.

Examples:

    # bell.py
    from qrisp import QuantumVariable, cx, h

    def prepare_state():
        qubits = QuantumVariable(2)
        h(qubits[0])
        cx(qubits[0], qubits[1])
        return qubits

    ./venv/bin/python tools/qrisp_statevector.py bell.py
    ./venv/bin/python tools/qrisp_statevector.py bell.py -o bell.state.json

Parameterized preparation functions can receive JSON arguments:

    ./venv/bin/python tools/qrisp_statevector.py ansatz.py \
        --function prepare --args '[0.25]' --kwargs '{"layers": 2}'

The dense ``amplitudes`` array is indexed by the printed binary basis string.
Qubit 0 is the leftmost (most-significant) bit. The first nonzero amplitude is
made real and nonnegative to remove physically irrelevant global phase.

This utility executes Qrisp Python source, not serialized Jasp MLIR. Qrisp's
builtin state-vector simulator operates on the live ``QuantumSession`` created
by the source program. State-vector comparison should normally be performed
before measurement, since measurement selects a stochastic trajectory.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable


FORMAT = "jasp-to-qir-statevector-v1"


def parse_json(value: str, expected_type: type, option: str) -> Any:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{option} is not valid JSON: {exc}") from exc
    if not isinstance(parsed, expected_type):
        raise ValueError(f"{option} must decode to {expected_type.__name__}")
    return parsed


def load_program(path: Path):
    module_name = f"_jasp-to-qir_qrisp_statevector_{abs(hash(path.resolve()))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load Python program: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.resolve().parent))
    try:
        with contextlib.redirect_stdout(sys.stderr):
            spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def walk_values(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from walk_values(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from walk_values(item)


def find_session(value: Any):
    try:
        from qrisp import QuantumSession
    except ImportError as exc:
        raise RuntimeError(
            "Qrisp is not installed; install the repository requirements first"
        ) from exc

    sessions: dict[int, Any] = {}
    for item in walk_values(value):
        session = item if isinstance(item, QuantumSession) else getattr(item, "qs", None)
        if isinstance(session, QuantumSession):
            sessions[id(session)] = session
    if not sessions:
        raise ValueError(
            "the preparation function did not return a QuantumSession or quantum value"
        )
    if len(sessions) != 1:
        raise ValueError("the preparation function returned values from multiple sessions")
    return next(iter(sessions.values()))


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


def state_document(state, source: Path, qubit_labels: list[str], threshold: float) -> dict:
    vector = canonicalize_global_phase(state, threshold)
    size = len(vector)
    n_qubits = size.bit_length() - 1
    if size != 1 << n_qubits:
        raise ValueError(f"state-vector length {size} is not a power of two")
    if len(qubit_labels) != n_qubits:
        qubit_labels = [f"q{index}" for index in range(n_qubits)]
    return {
        "format": FORMAT,
        "source": {"kind": "qrisp", "path": str(source.resolve())},
        "num_qubits": n_qubits,
        "qubits": qubit_labels,
        "basis_order": "qubit 0 is the leftmost (most-significant) bit",
        "global_phase": "first nonzero amplitude is real and nonnegative",
        "amplitudes": [[float(value.real), float(value.imag)] for value in vector],
    }


def write_document(document: dict, output: Path | None) -> None:
    encoded = json.dumps(document, indent=2, sort_keys=False) + "\n"
    if output is None:
        sys.stdout.write(encoded)
    else:
        output.write_text(encoded, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", type=Path, help="Qrisp Python source file")
    parser.add_argument(
        "--function", default="prepare_state", help="preparation function name"
    )
    parser.add_argument("--args", default="[]", help="JSON positional argument array")
    parser.add_argument("--kwargs", default="{}", help="JSON keyword argument object")
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
        if not math.isfinite(args.zero_threshold) or args.zero_threshold < 0:
            raise ValueError("--zero-threshold must be a finite nonnegative number")
        positional = parse_json(args.args, list, "--args")
        keyword = parse_json(args.kwargs, dict, "--kwargs")
        module = load_program(args.program)
        function = getattr(module, args.function, None)
        if not callable(function):
            raise ValueError(
                f"{args.program} has no callable named {args.function!r}"
            )
        with contextlib.redirect_stdout(sys.stderr):
            prepared = function(*positional, **keyword)
        session = find_session(prepared)
        with contextlib.redirect_stdout(sys.stderr):
            state = session.statevector(return_type="array")
        labels = [str(qubit) for qubit in session.qubits]
        document = state_document(
            state, args.program, labels, args.zero_threshold
        )
        write_document(document, args.output)
    except Exception as exc:
        parser.exit(1, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
