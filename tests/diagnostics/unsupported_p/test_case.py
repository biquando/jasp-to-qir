import unittest
from pathlib import Path

from tests import support


class UnsupportedPTest(unittest.TestCase):
    def test_reports_unsupported_gate(self) -> None:
        support.expect_conversion_failure(
            support.fixture(Path(__file__).parent),
            "Unsupported Jasp gate 'p'",
            support.temp_dir(),
        )
