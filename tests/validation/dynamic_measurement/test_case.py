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
        )
        output = support.convert_and_validate(
            fixture, "dynamic", support.temp_dir()
        )
        dynamic = support.require_contains(
            output,
            "__quantum__rt__result_array_allocate(i64 64",
            "call void @__quantum__qis__mz__body(ptr",
            "call i1 @__quantum__rt__read_result(ptr",
            "call void @__quantum__rt__result_array_record_output(i64 64",
            "call void @__quantum__rt__int_record_output(i64",
            "__quantum__rt__result_array_release(i64 64",
        )
        self.assertEqual(
            dynamic.count("call void @__quantum__rt__int_record_output"), 1
        )
        self.assertEqual(
            dynamic.count(
                "call void @__quantum__rt__result_array_record_output"
            ),
            1,
        )
