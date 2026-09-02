from pathlib import Path

from tests import support


class HelperMeasurementTest(support.ValidationTest):
    case_dir = Path(__file__).parent

    def test_conversion_and_validation(self) -> None:
        super().test_conversion_and_validation()
        dynamic = support.require_contains(
            support.output(self.case_dir, "dynamic"),
            "alloca [64 x ptr]",
            "call void @__quantum__rt__result_array_allocate(i64 64",
            "call void @__quantum__rt__result_array_release(i64 64",
        )
        self.assertNotIn("@__jasp__result_buffer", dynamic)
        self.assertEqual(
            dynamic.count("call void @__quantum__rt__result_array_allocate"), 1
        )
        self.assertEqual(
            dynamic.count("call void @__quantum__rt__result_array_release"), 1
        )
        support.require_adjacent(
            dynamic,
            "call void @__quantum__qis__mz__body",
            "call void @__quantum__rt__result_record_output",
            1,
        )
        self.assertNotIn("define void @measure_helper", dynamic)
