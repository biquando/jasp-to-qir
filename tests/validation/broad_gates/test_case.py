from pathlib import Path

from qrisp import (
    QuantumVariable, cx, cz, h, mcx, measure, reset, rx, ry, rz,
    s, s_dg, t, t_dg, x, y, z,
)
from tests import support


def qrisp_program():
    register = QuantumVariable(4)
    h(register[0])
    x(register[1])
    y(register[2])
    z(register[3])
    s(register[0])
    s_dg(register[1])
    t(register[2])
    t_dg(register[3])
    rx(0.125, register[0])
    ry(0.25, register[1])
    rz(0.5, register[2])
    cx(register[0], register[1])
    cz(register[1], register[2])
    mcx([register[0], register[1]], register[3], method="gray")
    reset(register[3])
    return measure(register)


class BroadGatesTest(support.ValidationTest):
    case_dir = Path(__file__).parent
