import unittest
from pathlib import Path

from qrisp import QuantumVariable, h, x, cx, QFT
from tests import support


def qrisp_program():
    q = QuantumVariable(5)
    h(q[1])
    cx(q[1], q[2])
    x(q[3])
    x(q[4])
    QFT(q)
    return q


class StatevectorQFTTest(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        case_dir = Path(__file__).parent
        support.verify_statevector_case(case_dir, 5, resource_modes=("dynamic",))
