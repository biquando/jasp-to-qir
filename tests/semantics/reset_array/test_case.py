import unittest
from pathlib import Path

from qrisp import QuantumVariable, cx, h, measure, reset, x
from tests import support


def qrisp_program():
    sentinel = QuantumVariable(1)
    register = QuantumVariable(2)
    x(sentinel)
    h(register[0])
    cx(register[0], register[1])
    reset(register)
    return measure(sentinel), measure(register)


class ArrayResetTest(unittest.TestCase):
    def test_measurement_equivalence(self) -> None:
        support.verify_measurement_case(
            Path(__file__).parent,
            qrisp_program,
            qubits=3,
            widths=(1, 2),
            expected=(1, 0, 0),
        )
