from pathlib import Path

from qrisp import QuantumVariable, h, measure
from qrisp.jasp import q_cond
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])
    condition = measure(register[0])

    def measure_second(data):
        measure(data[1])
        return data

    def leave_unchanged(data):
        return data

    register = q_cond(condition, measure_second, leave_unchanged, register)
    return condition


class ConditionalMeasurementTest(support.ValidationTest):
    case_dir = Path(__file__).parent
