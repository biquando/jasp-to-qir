import sys
import unittest
from pathlib import Path

from tests import support


class IgnoredGphaseTest(unittest.TestCase):
    def test_warns_and_drops_global_phase(self) -> None:
        for mode in support.RESOURCE_MODES:
            with self.subTest(mode=mode):
                output = support.temp_dir() / f"gphase-{mode}.ll"
                command = [sys.executable, support.DRIVER]
                if mode == "static":
                    command.append("--static")
                command.extend([support.fixture(Path(__file__).parent), output])
                result = support.run(command)
                support.run([sys.executable, support.VALIDATOR, output])
                support.run([support.OPT, "-passes=verify", "-disable-output", output])
                qir = output.read_text()
                self.assertNotIn("__quantum__qis__gphase", qir)
                calls = [line.strip() for line in qir.splitlines()
                         if "call void @__quantum__qis__" in line]
                self.assertEqual(len(calls), 2)
                self.assertIn("@__quantum__qis__h__body", calls[0])
                self.assertIn("@__quantum__qis__x__body", calls[1])
