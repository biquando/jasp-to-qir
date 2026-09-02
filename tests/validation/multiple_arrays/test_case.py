from pathlib import Path

from qrisp import QuantumVariable, cx, h, measure, x, z
from qrisp.jasp import q_cond
from tests import support


def qrisp_program():
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


class MultipleArraysTest(support.ValidationTest):
    case_dir = Path(__file__).parent
