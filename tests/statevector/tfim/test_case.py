import unittest
from pathlib import Path

from qrisp import QuantumVariable
from qrisp.operators import QubitOperator, X, Z
from tests import support


def qrisp_program():
    hamiltonian = QubitOperator()
    for index in range(4):
        hamiltonian += -0.8 * Z(index) * Z(index + 1)
    for index in range(5):
        hamiltonian += -1.2 * X(index)
    register = QuantumVariable(5)
    hamiltonian.trotterization(order=2)(register, t=1, steps=4)
    return register


class StatevectorTfimTest(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        case_dir = Path(__file__).parent
        support.verify_statevector_case(case_dir, 5)
