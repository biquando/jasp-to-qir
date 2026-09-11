"""Measurement must preserve both outcomes for subsequent gates and reads."""
import re
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
                    command = [sys.executable, support.DRIVER, "--verbose",
                               Path(__file__).with_name('input.mlir'), output]
                    if mode == 'static':
                        command.append('--static')
                    if enabled:
                        command.append('--require-mcmr')
                    support.run(command)
                    support.run([sys.executable, support.VALIDATOR, output])
                    text = output.read_text()
                    mresetz = '__quantum__qis__mresetz__body'
                    if enabled:
                        self.assertIn(f'call void @{mresetz}', text)
                        self.assertNotIn('call void @__quantum__qis__mz__body', text)
                        self.assertNotIn('call void @__quantum__qis__reset__body', text)
                        declaration = re.search(
                            rf'declare void @{mresetz}\(ptr, ptr writeonly\) #(\d+)',
                            text,
                        )
                        self.assertIsNotNone(declaration)
                        self.assertRegex(
                            text,
                            rf'attributes #{declaration.group(1)} = '
                            r'\{[^}]*"irreversible"[^}]*\}',
                        )
                    else:
                        self.assertNotIn(mresetz, text)
                    runner = build(output, build_dir=work / 'selene')
                    entries = list(runner.run(simulator=Quest(), n_qubits=2))
                    self.assertTrue(all(label.startswith("measurement_") for label, _ in entries))
                    bits = support.selene_result_bits(entries, (1, 1, 2, 2),
                                                      'mcmr', mode)
                    self.assertEqual(bits, [0, 1, 1, 0, 0, 1])
