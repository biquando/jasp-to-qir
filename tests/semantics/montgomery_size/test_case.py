import unittest
from pathlib import Path

import jax.numpy as jnp
from qrisp import QuantumBool, control, measure, x
from qrisp.jasp import q_fori_loop
from qrisp.alg_primitives.arithmetic.jasp_arithmetic.jasp_mod_tools import (
    smallest_power_of_two,
)
from tests import support


def qrisp_program():
    def check(n, valid):
        # Independent integer oracle: count powers of two strictly below n.
        expected = jnp.int64(0)
        for exponent in range(17):
            expected += jnp.int64(n > (1 << exponent))
        return valid & (smallest_power_of_two(n) == expected)

    valid = q_fori_loop(-2, 130, check, jnp.bool_(True))

    def check_boundary(exponent, valid):
        power = jnp.int64(1) << exponent
        return check(power + 1, check(power, check(power - 1, valid)))

    valid = q_fori_loop(1, 17, check_boundary, valid)
    failure = QuantumBool()
    with control(~valid):
        x(failure)
    return measure(failure[0])


class MontgomerySizeTest(unittest.TestCase):
    def test_integer_sizes_and_backend_compilation(self):
        case_dir = Path(__file__).parent
        support.verify_measurement_case(
            case_dir, qrisp_program, qubits=1, widths=(1,), expected=(0,),
        )
        for mode in support.RESOURCE_MODES:
            text = support.output(case_dir, mode).read_text()
            for intrinsic in ('llvm.log', 'llvm.ceil', 'llvm.ctpop'):
                self.assertNotIn(intrinsic, text)
