import unittest
from pathlib import Path

from qrisp import QuantumVariable, cx, h
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])
    cx(register[0], register[1])
    return register


class StatevectorBellTest(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        support.verify_statevector_case(Path(__file__).parent, 2)
