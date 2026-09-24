import unittest
from pathlib import Path

from qrisp import QuantumVariable, control, gphase, h
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])
    h(register[1])
    gphase(0.75, register[1])
    with control(register[0]):
        gphase(0.5, register[1])
    return register


class GlobalPhaseTest(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        support.verify_statevector_case(Path(__file__).parent, 2)
