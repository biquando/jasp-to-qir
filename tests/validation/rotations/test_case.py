from pathlib import Path

from qrisp import QuantumVariable, cx, h, measure, rz
from tests import support


def qrisp_program():
    register = QuantumVariable(3)
    h(register[0])
    cx(register[0], register[1])
    rz(0.25, register[2])
    cx(register[1], register[2])
    return measure(register)


class RotationsTest(support.ValidationTest):
    case_dir = Path(__file__).parent
