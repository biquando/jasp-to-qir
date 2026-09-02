from pathlib import Path

from qrisp import QuantumVariable, measure
from tests import support


def qrisp_program():
    register = QuantumVariable(20)
    return measure(register)


class ManyResultsTest(support.ValidationTest):
    case_dir = Path(__file__).parent

    def test_conversion_and_validation(self) -> None:
        super().test_conversion_and_validation()
        support.require_contains(
            support.output(self.case_dir),
            '@label10 = internal constant [10 x i8] c"result_10\\00"',
        )
