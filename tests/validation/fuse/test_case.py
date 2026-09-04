import unittest
from pathlib import Path

from tests import support


class FuseTest(unittest.TestCase):
    case_dir = Path(__file__).parent

    def test_requires_dynamic_resource_management(self) -> None:
        support.expect_conversion_failure(
            support.fixture(self.case_dir),
            "jasp.fuse requires dynamic resource management",
            support.temp_dir(),
            mode="static",
        )

    def test_lowers_scalar_and_array_operands(self) -> None:
        output = support.convert_and_validate(
            support.fixture(self.case_dir), "dynamic", support.temp_dir()
        )
        dynamic = support.require_contains(
            output,
            "alloca ptr, i64 2",
            "alloca ptr, i64 3",
            "alloca ptr, i64 4",
            "call void @__quantum__rt__qubit_release(ptr",
        )
        self.assertEqual(
            dynamic.count("call ptr @__quantum__rt__qubit_allocate(ptr null)"), 4
        )
        self.assertEqual(
            dynamic.count("call void @__quantum__rt__qubit_release(ptr"), 1
        )
