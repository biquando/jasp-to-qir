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
        )
        output = support.convert_and_validate(
            fixture, "dynamic", support.temp_dir()
        )
        text = support.require_contains(
            output,
            "alloca ptr, i64 %",
            "call ptr @__quantum__rt__qubit_allocate(ptr null)",
            "call void @__quantum__rt__qubit_release(ptr",
            '!"backwards_branching", i2 3',
        )
        self.assertNotIn("__quantum__rt__qubit_array_allocate", text)
