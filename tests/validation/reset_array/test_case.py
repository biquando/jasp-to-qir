from pathlib import Path

from qrisp import QuantumVariable, measure, reset
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    reset(register)
    return measure(register)


class ResetArrayTest(support.ValidationTest):
    case_dir = Path(__file__).parent
