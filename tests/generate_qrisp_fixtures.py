#!/usr/bin/env python3
"""Generate representative Jasp MLIR fixtures with Qrisp."""

import argparse
from pathlib import Path

from qrisp import *
from qrisp.operators import QubitOperator, X, Z
from qrisp.jasp import jrange, q_cond, q_while_loop, Jaspr


def basic():
    register = QuantumVariable(2)
    h(register[0])
    return measure(register)


def bell():
    register = QuantumVariable(2)
    h(register[0])
    cx(register[0], register[1])
    return measure(register)


def lifecycle():
    register = QuantumVariable(1)
    outcome = measure(register[0])
    register.delete()
    return outcome


def multiple_arrays():
    data = QuantumVariable(3)
    target = QuantumVariable(1)
    control = QuantumVariable(1)

    h(data[0])
    cx(data[0], data[1])
    cx(data[1], data[2])
    h(control[0])
    condition = measure(control[0])

    def apply_x(register):
        x(register[1])
        return register

    def apply_z(register):
        z(register[2])
        return register

    data = q_cond(condition, apply_x, apply_z, data)
    cx(data[0], target[0])
    cx(data[1], target[0])
    target_outcome = measure(target[0])

    def correct_data(register):
        x(register[1])
        return register

    def leave_unchanged(register):
        return register

    data = q_cond(target_outcome, leave_unchanged, correct_data, data)
    return condition, target_outcome, measure(data)


def tfim():
    n = 5
    J = 0.8
    B = 1.2
    t = 1
    steps = 4

    H = QubitOperator()
    for i in range(n-1):
        H += -J * Z(i) * Z(i+1)
    for i in range(n):
        H += -B * X(i)

    U = H.trotterization(order=2)

    register = QuantumVariable(n)
    U(register, t=t, steps=steps)

    return measure(register)


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


def statevector_bell():
    register = QuantumVariable(2)
    h(register[0])
    cx(register[0], register[1])
    return register


def statevector_broad_gates():
    register = QuantumVariable(4)

    h(register[0])
    h(register[1])
    x(register[2])
    y(register[3])
    z(register[0])
    s(register[0])
    s_dg(register[1])
    t(register[2])
    t_dg(register[3])
    rx(0.125, register[0])
    ry(-0.25, register[1])
    rz(0.5, register[2])
    cx(register[0], register[2])
    cz(register[1], register[3])
    mcx([register[0], register[1]], register[3], method="gray")
    return register


def statevector_multiple_arrays():
    data = QuantumVariable(3)
    ancilla = QuantumVariable(2)
    target = QuantumVariable(1)

    h(data[0])
    rx(0.375, data[1])
    for index in jrange(2):
        cx(data[index], ancilla[index])
        ry(0.25, ancilla[index])
    cz(ancilla[1], target[0])
    return data, ancilla, target


def statevector_tfim():
    n = 5
    J = 0.8
    B = 1.2
    t = 1
    steps = 4

    H = QubitOperator()
    for i in range(n-1):
        H += -J * Z(i) * Z(i+1)
    for i in range(n):
        H += -B * X(i)

    U = H.trotterization(order=2)

    register = QuantumVariable(n)
    U(register, t=t, steps=steps)

    return register


def measurement_basis_array():
    register = QuantumVariable(4)
    x(register[0])
    y(register[2])
    return measure(register)


def measurement_feedback():
    data = QuantumVariable(2)
    controls = QuantumVariable(2)
    x(controls[0])
    true_result = measure(controls[0])
    false_result = measure(controls[1])

    def set_first(register):
        x(register[0])
        return register

    def phase_first(register):
        z(register[0])
        return register

    data = q_cond(true_result, set_first, phase_first, data)

    def phase_second(register):
        z(register[1])
        return register

    def set_second(register):
        x(register[1])
        return register

    data = q_cond(false_result, phase_second, set_second, data)
    return true_result, false_result, measure(data)


def measurement_reset():
    register = QuantumVariable(2)
    h(register[0])
    reset(register[0])
    x(register[1])
    return measure(register)


def write_fixture(function, output: Path) -> None:
    jaspr = make_jaspr(function)()
    assert type(jaspr) == Jaspr
    mlir = str(jaspr.to_mlir(lower_stablehlo=True))
    output.write_text(mlir.rstrip() + "\n", encoding="utf-8")


FIXTURES = {
    "basic.mlir": basic,
    "bell.mlir": bell,
    "lifecycle.mlir": lifecycle,
    "multiple_arrays.mlir": multiple_arrays,
    "tfim.mlir": tfim,
    "rotations.mlir": rotations,
    "adaptive.mlir": adaptive,
    "loop.mlir": loop,
    "reset_chain.mlir": reset_chain,
    "reset_array.mlir": reset_array,
    "many_results.mlir": many_results,
    "conditional_measurement.mlir": conditional_measurement,
    "broad_gates.mlir": broad_gate_set,
    "measurement_feedback_loop.mlir": measurement_feedback_loop,
}


STATEVECTOR_CASES = {
    "statevector_bell.mlir": {
        "function": statevector_bell,
        "qubits": 2,
    },
    "statevector_broad_gates.mlir": {
        "function": statevector_broad_gates,
        "qubits": 4,
    },
    "statevector_multiple_arrays.mlir": {
        "function": statevector_multiple_arrays,
        "qubits": 6,
    },
    "statevector_tfim.mlir": {
        "function": statevector_tfim,
        "qubits": 5,
    },
}


MEASUREMENT_CASES = {
    "measurement_basis_array.mlir": {
        "function": measurement_basis_array,
        "qubits": 4,
        "widths": (4,),
        "expected": (1, 0, 1, 0),
    },
    "measurement_feedback.mlir": {
        "function": measurement_feedback,
        "qubits": 4,
        "widths": (1, 1, 2),
        "expected": (1, 0, 1, 1),
    },
    "measurement_reset.mlir": {
        "function": measurement_reset,
        "qubits": 2,
        "widths": (2,),
        "expected": (0, 1),
    },
}


FIXTURES.update(
    {
        name: case["function"]
        for name, case in (*STATEVECTOR_CASES.items(), *MEASUREMENT_CASES.items())
    }
)


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
