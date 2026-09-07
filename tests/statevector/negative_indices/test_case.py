import unittest
from pathlib import Path

from qrisp import QuantumVariable, cx, h, ry, rz
from qrisp.jasp import jrange
from tests import support


def qrisp_program():
    register = QuantumVariable(5)
    h(register[-1])
    ry(0.37, register[-5])
    middle = register[1:4]
    cx(register[-1], middle[-1])
    for i in jrange(3):
        ry(0.21 * (i + 1), middle[i - 3])
        rz(0.17 * (i + 1), register[i])
    return register


class NegativeIndicesTest(unittest.TestCase):
    def test_statevector_equivalence(self):
        support.verify_statevector_case(Path(__file__).parent, 5)
