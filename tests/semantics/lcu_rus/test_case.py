"""LCU(I + X)|1> prepares |+>; an X-basis measurement must return zero.

Qrisp's inner_LCU is wrapped with its RUS decorator. Heralds are random,
so compare termination/output semantics rather than matching random streams
or retry counts.
https://qrisp.eu/reference/Primitives/generated/qrisp.LCU.html
"""
import contextlib
import io
import unittest
from pathlib import Path

from qrisp import QuantumVariable, h, inner_LCU, measure, reset, x
from qrisp.jasp import RUS
from tests import support


def prepare_operand():
    operand = QuantumVariable(1)
    x(operand)
    return operand


def identity(operand):
    pass


@RUS
def lcu_trial():
    herald, operand = inner_LCU(prepare_operand, h, [identity, x])
    success = measure(herald[0]) == 0
    # The public LCU wrapper in the installed Qrisp leaves this register live
    # in generated MLIR. Explicit cleanup bounds resources across retries.
    reset(herald)
    herald.delete()
    return success, operand


def qrisp_program():
    operand = lcu_trial()
    h(operand)
    return measure(operand[0])


class LcuRusTest(unittest.TestCase):
    def test_successful_output_and_retry_trace(self):
        from qrisp.jasp import jaspify
        from selene_sim import Quest, build

        shots = 16
        simulate = jaspify(qrisp_program)
        qrisp_results = []
        with contextlib.redirect_stdout(io.StringIO()):
            for shot in range(shots):
                with self.subTest(simulator='Qrisp', shot=shot):
                    value = support.exact_integer(simulate(), 'LCU output')
                    qrisp_results.append(value)
                    self.assertEqual(value, 0)

        # The generated LCU helpers allocate runtime-sized registers, requiring
        # dynamic mode. Four live qubits suffice regardless of the retry count.
        qir = support.output(Path(__file__).parent, 'dynamic')
        runner = build(qir, build_dir=qir.parent / 'selene')
        rows = []
        for shot in range(shots):
            with self.subTest(simulator='QIR', shot=shot):
                entries = list(runner.run(
                    simulator=Quest(random_seed=7 + shot), n_qubits=4, timeout=30.0,
                ))
                bits = support.selene_result_bits(
                    entries, (1,) * len(entries), 'LCU/RUS', 'dynamic',
                )

                # Any number of failed heralds (1), then success (0), then the
                # independent X-basis output check (0). No seed-specific counts.
                self.assertGreaterEqual(len(bits), 2)
                self.assertEqual(bits[:-2], [1] * (len(bits) - 2))
                self.assertEqual(bits[-2:], [0, 0])
                rows.append((shot, qrisp_results[shot], bits[-1], len(bits) - 2))
        self.assertEqual(len(rows), shots)
        support.report_table(
            'Measurement: semantics/lcu_rus',
            ['shot', 'Qrisp', 'Dynamic QIR', 'QIR retries'], rows,
        )
