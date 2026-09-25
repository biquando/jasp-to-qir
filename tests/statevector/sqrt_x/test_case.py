import unittest
from pathlib import Path

from qrisp import QuantumVariable, invert, sx
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    sx(register[0])
    with invert():
        sx(register[1])
    return register


class StatevectorSqrtXTest(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        support.verify_statevector_case(Path(__file__).parent, 2)
