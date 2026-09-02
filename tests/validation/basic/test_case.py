import sys
from pathlib import Path

from qrisp import QuantumVariable, h, measure
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])
    return measure(register)


class BasicTest(support.ValidationTest):
    case_dir = Path(__file__).parent

    def test_conversion_and_validation(self) -> None:
        super().test_conversion_and_validation()
        explicit = support.temp_dir() / "basic.explicit-static.ll"
        support.run([sys.executable, support.DRIVER, self.case_dir / "input.mlir", explicit])
        self.assertEqual(support.output(self.case_dir).read_bytes(), explicit.read_bytes())
        dynamic = support.require_contains(
            support.output(self.case_dir, "dynamic"),
            '!"dynamic_qubit_management", i1 true',
            '!"dynamic_result_management", i1 true',
            '!"arrays", i1 true',
            "__quantum__rt__qubit_array_allocate(i64 2",
            "__quantum__rt__result_array_allocate(i64 2",
            "__quantum__rt__result_array_record_output(i64 2",
            "__quantum__rt__result_array_release(i64 2",
        )
        self.assertNotIn("required_num_", dynamic)
        self.assertNotIn("inttoptr", dynamic)
