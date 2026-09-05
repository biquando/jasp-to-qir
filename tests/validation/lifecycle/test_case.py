from pathlib import Path

from qrisp import QuantumVariable, measure
from tests import support


def qrisp_program():
    register = QuantumVariable(1)
    outcome = measure(register[0])
    register.delete()
    return outcome


class LifecycleTest(support.ValidationTest):
    case_dir = Path(__file__).parent
