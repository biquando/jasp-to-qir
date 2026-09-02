from pathlib import Path

from tests import support


class SliceTest(support.ValidationTest):
    case_dir = Path(__file__).parent

    def test_conversion_and_validation(self) -> None:
        super().test_conversion_and_validation()
        dynamic = support.require_contains(
            support.output(self.case_dir, "dynamic"),
            "getelementptr ptr, ptr",
            "icmp slt i64",
            "select i1",
            "call void @__quantum__rt__qubit_release(ptr",
        )
        self.assertNotIn("llvm.smin", dynamic)
        self.assertNotIn("llvm.smax", dynamic)
        self.assertNotIn("nocreateundeforpoison", dynamic)
        self.assertEqual(
            dynamic.count("call void @__quantum__rt__qubit_release(ptr"), 1
        )
