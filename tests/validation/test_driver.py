"""Public driver options and filesystem behavior, independent of LLVM spelling."""
import sys
import tempfile
import unittest
from pathlib import Path

from tests import support


class DriverTest(unittest.TestCase):
    def test_intermediate_cleanup_and_retention(self):
        for keep in (False, True):
            with self.subTest(keep=keep):
                work = Path(tempfile.mkdtemp(dir=support.temp_dir()))
                output = work / 'output.ll'
                sentinel = work / 'unrelated.txt'
                sentinel.write_text('keep me')
                command = [sys.executable, support.DRIVER,
                           support.TESTS / 'validation/basic/input.mlir', output]
                if keep:
                    command.append('--keep-intermediates')
                support.run(command)
                self.assertTrue(output.is_file())
                self.assertEqual(sentinel.read_text(), 'keep me')
                intermediates = set(work.iterdir()) - {output, sentinel}
                if keep:
                    self.assertTrue(intermediates)
                    self.assertTrue(any(p.suffix == '.mlir' for p in intermediates))
                else:
                    self.assertEqual(intermediates, set())

    def test_resource_mode_selection(self):
        case_dir = support.TESTS / 'validation/basic'
        for mode in support.RESOURCE_MODES:
            with self.subTest(mode=mode):
                value = 'true' if mode == 'dynamic' else 'false'
                support.require_contains(
                    support.output(case_dir, mode),
                    f'!"dynamic_qubit_management", i1 {value}',
                    f'!"dynamic_result_management", i1 {value}',
                )

    def test_custom_result_buffer(self):
        work = Path(tempfile.mkdtemp(dir=support.temp_dir()))
        output = work / 'output.ll'
        support.run([sys.executable, support.DRIVER, '--result-buffer-size', '7',
                     support.TESTS / 'validation/basic/input.mlir', output])
        support.run([sys.executable, support.VALIDATOR, output])
        # The requested capacity is an ABI contract, unlike SSA names or layout.
        support.require_contains(output, '__quantum__rt__result_array_allocate(i64 7',
                                 '__quantum__rt__result_array_release(i64 7')
