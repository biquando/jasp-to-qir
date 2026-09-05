import unittest
from pathlib import Path

from qrisp import QuantumFloat, h
from tests import support


def qrisp_program():
    q = QuantumFloat(3)
    h(q[0])
    q += 3
    return q


class StatevectorAdderTest(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        case_dir = Path(__file__).parent
        support.verify_statevector_case(case_dir, 5, resource_modes=("dynamic",))
