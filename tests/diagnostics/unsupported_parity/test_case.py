import unittest
from pathlib import Path

from tests import support


class UnsupportedParityTest(unittest.TestCase):
    def test_reports_unsupported_operation(self) -> None:
        support.expect_conversion_failure(
            support.fixture(Path(__file__).parent),
            "Unsupported Jasp operation 'jasp.parity'",
            support.temp_dir(),
        )
