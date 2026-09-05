from pathlib import Path

from qrisp import QuantumVariable, measure
from tests import support


def qrisp_program():
    register = QuantumVariable(20)
    return measure(register)


class ManyResultsTest(support.ValidationTest):
    case_dir = Path(__file__).parent
