import unittest
from pathlib import Path

from tests import support


class UnsupportedFuseTest(unittest.TestCase):
    def test_reports_unsupported_operation(self) -> None:
        support.expect_conversion_failure(
            support.fixture(Path(__file__).parent),
            "Unsupported Jasp operation 'jasp.fuse'",
            support.temp_dir(),
        )
