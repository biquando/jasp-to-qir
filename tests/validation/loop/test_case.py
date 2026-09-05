from pathlib import Path

from qrisp import QuantumVariable, h, measure
from qrisp.jasp import jrange
from tests import support


def qrisp_program():
    register = QuantumVariable(3)
    for index in jrange(register.size):
        h(register[index])
    return measure(register)


class LoopTest(support.ValidationTest):
    case_dir = Path(__file__).parent
