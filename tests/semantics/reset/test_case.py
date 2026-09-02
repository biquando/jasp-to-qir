import unittest
from pathlib import Path

from qrisp import QuantumVariable, h, measure, reset, x
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])
    reset(register[0])
    x(register[1])
    return measure(register)


class MeasurementResetTest(unittest.TestCase):
    def test_measurement_equivalence(self) -> None:
        support.verify_measurement_case(
            Path(__file__).parent,
            qrisp_program,
            qubits=2,
            widths=(2,),
            expected=(0, 1),
        )
