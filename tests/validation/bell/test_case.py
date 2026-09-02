from pathlib import Path

from qrisp import QuantumVariable, cx, h, measure
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])
    cx(register[0], register[1])
    return measure(register)


class BellTest(support.ValidationTest):
    case_dir = Path(__file__).parent
