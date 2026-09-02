import unittest
from pathlib import Path

from qrisp import QuantumVariable, measure, x, z
from qrisp.jasp import q_cond
from tests import support


def qrisp_program():
    data = QuantumVariable(2)
    controls = QuantumVariable(2)
    x(controls[0])
    true_result = measure(controls[0])
    false_result = measure(controls[1])

    def set_first(register):
        x(register[0])
        return register

    def phase_first(register):
        z(register[0])
        return register

    data = q_cond(true_result, set_first, phase_first, data)

    def phase_second(register):
        z(register[1])
        return register

    def set_second(register):
        x(register[1])
        return register

    data = q_cond(false_result, phase_second, set_second, data)
    return true_result, false_result, measure(data)


class MeasurementFeedbackTest(unittest.TestCase):
    def test_measurement_equivalence(self) -> None:
        support.verify_measurement_case(
            Path(__file__).parent,
            qrisp_program,
            qubits=4,
            widths=(1, 1, 2),
            expected=(1, 0, 1, 1),
        )
