"""Measurement must preserve both outcomes for subsequent gates and reads."""
import sys
import tempfile
import unittest
from pathlib import Path

from selene_sim import Quest, build
from tests import support


class MeasurementRestorationTest(unittest.TestCase):
    def test_reuse_after_scalar_and_array_measurement(self):
        for mode in support.RESOURCE_MODES:
            for enabled in (False, True):
                with self.subTest(mode=mode, require_mcmr=enabled):
                    work = Path(tempfile.mkdtemp(dir=support.temp_dir()))
                    output = work / 'output.ll'
                    command = [sys.executable, support.DRIVER,
                               Path(__file__).with_name('input.mlir'), output]
                    if mode == 'static':
                        command.append('--static')
                    if enabled:
                        command.append('--require-mcmr')
                    support.run(command)
                    support.run([sys.executable, support.VALIDATOR, output])
                    self.assertEqual('__quantum__qis__reset__body' in output.read_text(),
                                     enabled)
                    runner = build(output, build_dir=work / 'selene')
                    entries = list(runner.run(simulator=Quest(), n_qubits=2))
                    bits = support.selene_result_bits(entries, (1, 1, 2, 2),
                                                      'mcmr', mode)
                    self.assertEqual(bits, [0, 1, 1, 0, 0, 1])
