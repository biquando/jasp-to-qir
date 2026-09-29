import unittest
from pathlib import Path

from qrisp import QuantumVariable, cx, h, u3, x
from qrisp.jasp import jrange
from tests import support


def qrisp_program():
    register = QuantumVariable(3)
    x(register[1])
    h(register[2])
    # Distinct angles on |0>, |1>, and a superposition expose parameter swaps.
    u3(0.37, -0.61, 0.83, register[0])
    u3(-0.29, 0.47, -0.71, register[1])
    u3(0.53, -0.19, 0.97, register[2])
    cx(register[2], register[0])
    # Exercise runtime parameters and an entangled input without unrolling.
    for index in jrange(3):
        u3(0.13 * index, -0.23 * index, 0.31 * index, register[0])
    return register


class StatevectorU3Test(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        support.verify_statevector_case(Path(__file__).parent, 3)
