from pathlib import Path

from qrisp import QuantumVariable, cx, h, measure, reset, x
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])
    x(register[1])
    reset(register[0])
    cx(register[0], register[1])
    return measure(register)


class ResetChainTest(support.ValidationTest):
    case_dir = Path(__file__).parent
