from pathlib import Path

from qrisp import QuantumVariable, h, measure, x, z
from qrisp.jasp import q_cond
from tests import support


def qrisp_program():
    data = QuantumVariable(2)
    control = QuantumVariable(1)
    h(data[0])
    h(control[0])
    outcome = measure(control[0])

    def apply_x(register):
        x(register[1])
        return register

    def apply_z(register):
        z(register[1])
        return register

    data = q_cond(outcome, apply_x, apply_z, data)
    return outcome, measure(data)


class AdaptiveTest(support.ValidationTest):
    case_dir = Path(__file__).parent

    def test_conversion_and_validation(self) -> None:
        super().test_conversion_and_validation()
        support.require_contains(support.output(self.case_dir), "br i1")
