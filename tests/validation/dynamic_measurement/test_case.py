import unittest
from pathlib import Path

from tests import support


class DynamicMeasurementTest(unittest.TestCase):
    case_dir = Path(__file__).parent

    def test_runtime_measurement_size_requires_dynamic_mode(self) -> None:
        fixture = support.fixture(self.case_dir)
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
