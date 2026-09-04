import unittest
from pathlib import Path

from tests import support


class InvalidMeasureTest(unittest.TestCase):
    def test_rejects_invalid_result_type(self) -> None:
        support.expect_conversion_failure(
            support.fixture(Path(__file__).parent),
            "requires result type 'tensor<i1>' for operand type '!jasp.Qubit'",
            support.temp_dir(),
            mode="static",
        )
