"""GVN reuses handle loads without eliminating or reordering quantum calls."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

from llvmlite import binding
from tests import support


class RedundantQubitLoadsTest(unittest.TestCase):
    def test_handle_reuse(self):
        for mode in support.RESOURCE_MODES:
            with self.subTest(mode=mode):
                work = Path(tempfile.mkdtemp(dir=support.temp_dir()))
                output = work / 'output.ll'
                support.run([sys.executable, support.DRIVER,
                             Path(__file__).with_name('input.mlir'), output,
                             '--keep-intermediates',
                             *(['--static'] if mode == 'static' else [])])
                support.run([sys.executable, support.VALIDATOR, output])
                before = (work / 'output.7.unoptimized.ll').read_text()
                after = output.read_text()
                calls = r'call void @(__quantum__qis__\w+)\('
                self.assertEqual(re.findall(calls, before), re.findall(calls, after))
                if mode == 'dynamic':
                    self.assertGreaterEqual(before.count(' = load ptr,') -
                                            after.count(' = load ptr,'), 4)
                    cnots = re.findall(r'call void @__quantum__qis__cnot__body\(ptr (\S+), ptr (\S+)\)', after)
                    self.assertEqual(len(cnots), 2)
                    self.assertEqual(cnots[0], cnots[1])
                    self.assertRegex(after, rf'call void @__quantum__qis__rz__body\(double [^,]+, ptr {re.escape(cnots[0][1])}\)')
                    self.assertIn(f'call void @__quantum__qis__x__body(ptr {cnots[0][0]})', after)
                module = binding.parse_assembly(after)
                module.verify()
                for gate in ('cnot', 'rz', 'reset', 'x'):
                    attrs = b' '.join(module.get_function(f'__quantum__qis__{gate}__body').attributes)
                    self.assertIn(b'memory(inaccessiblemem: readwrite)', attrs)
                for name in ('__quantum__qis__mz__body', '__quantum__rt__read_result'):
                    attrs = b' '.join(module.get_function(name).attributes)
                    self.assertNotIn(b'memory(inaccessiblemem: readwrite)', attrs)
                self.assertEqual(after.splitlines()[:2],
                                 ["; ModuleID = 'output.ll'", 'source_filename = "input.mlir"'])
