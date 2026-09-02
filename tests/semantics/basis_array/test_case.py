import unittest
from pathlib import Path

from qrisp import QuantumVariable, measure, x, y
from tests import support


def qrisp_program():
    register = QuantumVariable(4)
    x(register[0])
    y(register[2])
    return measure(register)


class MeasurementBasisArrayTest(unittest.TestCase):
    def test_measurement_equivalence(self) -> None:
        support.verify_measurement_case(
            Path(__file__).parent,
            qrisp_program,
            qubits=4,
            widths=(4,),
            expected=(1, 0, 1, 0),
        )
