import unittest
from pathlib import Path

from qrisp import QuantumVariable, cx, cz, h, rx, ry
from qrisp.jasp import jrange
from tests import support


def qrisp_program():
    data = QuantumVariable(3)
    ancilla = QuantumVariable(2)
    target = QuantumVariable(1)
    h(data[0])
    rx(0.375, data[1])
    for index in jrange(2):
        cx(data[index], ancilla[index])
        ry(0.25, ancilla[index])
    cz(ancilla[1], target[0])
    return data, ancilla, target


class StatevectorMultipleArraysTest(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        support.verify_statevector_case(Path(__file__).parent, 6)
