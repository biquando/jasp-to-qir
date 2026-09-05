import unittest
from pathlib import Path

from tests import support


class DynamicAllocationTest(unittest.TestCase):
    def test_runtime_size_requires_dynamic_mode(self) -> None:
        fixture = support.fixture(Path(__file__).parent)
        support.expect_conversion_failure(
            fixture,
            "static QIR resource management requires a compile-time constant "
            "qubit count",
            support.temp_dir(),
            mode="static",
        )
        output = support.convert_and_validate(
            fixture, "dynamic", support.temp_dir()
        )
