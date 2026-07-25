#!/usr/bin/env python3
"""Generate representative Jasp MLIR fixtures with Qrisp."""

import argparse
from pathlib import Path

from qrisp import (
    QuantumVariable,
    cx,
    cz,
    h,
    make_jaspr,
    mcx,
    measure,
    reset,
    rx,
    ry,
    rz,
    s,
    s_dg,
    t,
    t_dg,
    x,
    y,
    z,
)
from qrisp.jasp import jrange, q_cond, q_while_loop, Jaspr


def rotations():
    register = QuantumVariable(3)
    h(register[0])
    cx(register[0], register[1])
    rz(0.25, register[2])
    cx(register[1], register[2])
    return measure(register)


def adaptive():
    data = QuantumVariable(2)
    control = QuantumVariable(1)
    h(data[0])
    h(control[0])
    outcome = measure(control[0])

    def apply_x(register):
        x(register[1])
        return register

    def apply_z(register):
        z(register[1])
        return register

    data = q_cond(outcome, apply_x, apply_z, data)
    return outcome, measure(data)


def loop():
    register = QuantumVariable(3)
    for index in jrange(register.size):
        h(register[index])
    return measure(register)


def reset_chain():
    register = QuantumVariable(2)
    h(register[0])
    x(register[1])
    reset(register[0])
    cx(register[0], register[1])
    return measure(register)


def reset_array():
    register = QuantumVariable(2)
    reset(register)
    return measure(register)


def many_results():
    register = QuantumVariable(20)
    return measure(register)


def conditional_measurement():
    register = QuantumVariable(2)
    h(register[0])
    condition = measure(register[0])

    def measure_second(data):
        measure(data[1])
        return data

    def leave_unchanged(data):
        return data

    register = q_cond(
        condition, measure_second, leave_unchanged, register
    )
    return condition


def broad_gate_set():
    register = QuantumVariable(4)

    h(register[0])
    x(register[1])
    y(register[2])
    z(register[3])

    s(register[0])
    s_dg(register[1])
    t(register[2])
    t_dg(register[3])

    rx(0.125, register[0])
    ry(0.25, register[1])
    rz(0.5, register[2])

    cx(register[0], register[1])
    cz(register[1], register[2])
    mcx([register[0], register[1]], register[3], method="gray")

    reset(register[3])
    return measure(register)


def measurement_feedback_loop():
    register = QuantumVariable(2)
    h(register[0])

    def condition(value):
        return value[0] < 2

    def body(value):
        index, total, data = value
        cx(data[0], data[1])
        total += measure(data[index])
        return index + 1, total, data

    _, total, register = q_while_loop(condition, body, (0, 0, register))
    return total, measure(register)


def write_fixture(function, output: Path) -> None:
    jaspr = make_jaspr(function)()
    assert type(jaspr) == Jaspr
    mlir = str(jaspr.to_mlir(lower_stablehlo=True))
    output.write_text(mlir.rstrip() + "\n", encoding="utf-8")


FIXTURES = {
    "adaptive.mlir": adaptive,
    "broad_gates.mlir": broad_gate_set,
    "conditional_measurement.mlir": conditional_measurement,
    "loop.mlir": loop,
    "many_results.mlir": many_results,
    "measurement_feedback_loop.mlir": measurement_feedback_loop,
    "reset.mlir": reset_chain,
    "reset_array.mlir": reset_array,
    "rotations.mlir": rotations,
}


def main() -> None:
    default_output = Path(__file__).resolve().parent / "fixtures/qrisp"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output,
        help=f"fixture destination (default: {default_output})",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, function in FIXTURES.items():
        write_fixture(function, args.output_dir / name)


if __name__ == "__main__":
    main()
