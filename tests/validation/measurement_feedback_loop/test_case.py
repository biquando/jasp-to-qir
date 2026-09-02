from pathlib import Path

from qrisp import QuantumVariable, cx, h, measure
from qrisp.jasp import q_while_loop
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])

    def condition(value):
        return value[0] < 2

    def body(value):
        index, total, data = value
        cx(data[0], data[1])
        total += measure(data[index])
        return index + 1, total, data

    _, total, register = q_while_loop(condition, body, (0, 0, register))
    return total, measure(register)


class MeasurementFeedbackLoopTest(support.ValidationTest):
    case_dir = Path(__file__).parent
