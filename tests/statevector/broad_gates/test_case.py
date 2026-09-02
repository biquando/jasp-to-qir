import unittest
from pathlib import Path

from qrisp import (
    QuantumVariable, cx, cz, h, mcx, rx, ry, rz, s, s_dg, t, t_dg, x, y, z,
)
from tests import support


def qrisp_program():
    register = QuantumVariable(4)
    h(register[0])
    h(register[1])
    x(register[2])
    y(register[3])
    z(register[0])
    s(register[0])
    s_dg(register[1])
    t(register[2])
    t_dg(register[3])
    rx(0.125, register[0])
    ry(-0.25, register[1])
    rz(0.5, register[2])
    cx(register[0], register[2])
    cz(register[1], register[3])
    mcx([register[0], register[1]], register[3], method="gray")
    return register


class StatevectorBroadGatesTest(unittest.TestCase):
    def test_statevector_equivalence(self) -> None:
        support.verify_statevector_case(Path(__file__).parent, 4)
