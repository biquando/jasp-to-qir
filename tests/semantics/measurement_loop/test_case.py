import unittest
from pathlib import Path

from qrisp import QuantumVariable, measure, x
from qrisp.jasp import q_while_loop
from tests import support


def qrisp_program():
    register = QuantumVariable(1)
    x(register[0])

    def condition(value):
        return value[0] < 3

    def body(value):
        index, packed, data = value
        bit = measure(data[0])
        x(data[0])
        return index + 1, packed | (bit << index), data

    _, packed, _ = q_while_loop(condition, body, (0, 0, register))
    # Every measurement is returned separately in its execution order.
    return packed & 1, (packed >> 1) & 1, (packed >> 2) & 1


class MeasurementLoopTest(unittest.TestCase):
    def test_loop_records_each_iteration_in_order(self):
        support.verify_measurement_case(
            Path(__file__).parent, qrisp_program, qubits=1,
            widths=(1, 1, 1), expected=(1, 0, 1),
        )
