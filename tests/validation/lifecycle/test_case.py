from pathlib import Path

from qrisp import QuantumVariable, measure
from tests import support


def qrisp_program():
    register = QuantumVariable(1)
    outcome = measure(register[0])
    register.delete()
    return outcome


class LifecycleTest(support.ValidationTest):
    case_dir = Path(__file__).parent

    def test_conversion_and_validation(self) -> None:
        super().test_conversion_and_validation()
        support.require_contains(
            support.output(self.case_dir, "dynamic"),
            "__quantum__rt__qubit_array_allocate(i64 1",
            "__quantum__rt__qubit_array_release(i64 1",
        )
