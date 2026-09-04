import unittest
from pathlib import Path

from tests import support


class UnsupportedGphaseTest(unittest.TestCase):
    def test_reports_unsupported_gate(self) -> None:
        support.expect_conversion_failure(
            support.fixture(Path(__file__).parent),
            "Unsupported Jasp gate 'gphase'",
            support.temp_dir(),
            mode="static",
        )
