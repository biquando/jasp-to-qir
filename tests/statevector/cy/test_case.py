import unittest
from pathlib import Path

from qrisp import QuantumVariable, cy, h, ry, s
from tests import support


def qrisp_program():
    register = QuantumVariable(3)
    h(register[0])
    ry(0.41, register[1])
    s(register[1])
    h(register[2])
    # Superposed controls and complex targets expose relative-phase errors.
    cy(register[0], register[1])
    cy(register[1], register[2])
    cy(register[2], register[0])
    return register


class StatevectorCYTest(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        support.verify_statevector_case(Path(__file__).parent, 3)
