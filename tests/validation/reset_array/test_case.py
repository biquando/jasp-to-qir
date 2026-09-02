from pathlib import Path

from qrisp import QuantumVariable, measure, reset
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    reset(register)
    return measure(register)


class ResetArrayTest(support.ValidationTest):
    case_dir = Path(__file__).parent

    def test_conversion_and_validation(self) -> None:
        super().test_conversion_and_validation()
        text = support.require_contains(
            support.output(self.case_dir),
            "declare void @__quantum__qis__reset__body(ptr)",
        )
        self.assertNotIn("__quantum__qis__reset__body({", text)
        self.assertNotIn("declare void @__quantum__qis__reset__body(ptr) #", text)
