import unittest
from pathlib import Path

from qrisp import QuantumVariable, measure, x
from qrisp.jasp import q_cond
from tests import support


def qrisp_program():
    register = QuantumVariable(3)
    x(register[0])
    x(register[2])
    true_result = measure(register[0])
    false_result = measure(register[1])

    def measure_one(data):
        return measure(data[2])

    def measure_zero(data):
        return measure(data[1])

    first = q_cond(true_result, measure_one, measure_zero, register)
    second = q_cond(false_result, measure_one, measure_zero, register)
    return true_result, false_result, first, second


class ConditionalOutputTest(unittest.TestCase):
    def test_only_taken_branches_record_measurements(self):
        support.verify_measurement_case(
            Path(__file__).parent, qrisp_program, qubits=3,
            widths=(1, 1, 1, 1), expected=(1, 0, 1, 0),
        )
