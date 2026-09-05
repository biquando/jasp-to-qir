from pathlib import Path

from qrisp import QuantumVariable, h, measure
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])
    return measure(register)


class BasicTest(support.ValidationTest):
    case_dir = Path(__file__).parent
