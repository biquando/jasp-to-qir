import unittest
from pathlib import Path

from tests import support


class UnsupportedSliceTest(unittest.TestCase):
    def test_reports_unsupported_operation(self) -> None:
        support.expect_conversion_failure(
            support.fixture(Path(__file__).parent),
            "Unsupported Jasp operation 'jasp.slice'",
            support.temp_dir(),
        )
