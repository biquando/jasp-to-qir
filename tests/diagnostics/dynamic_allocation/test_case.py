import unittest
from pathlib import Path

from tests import support


class DynamicAllocationTest(unittest.TestCase):
    def test_requires_compile_time_size(self) -> None:
        message = "QIR array backing storage requires a compile-time constant size"
        for mode in ("static", "dynamic"):
            support.expect_conversion_failure(
                support.fixture(Path(__file__).parent),
                message,
                support.temp_dir(),
                mode=mode,
            )
