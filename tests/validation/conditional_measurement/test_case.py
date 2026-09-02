from pathlib import Path

from qrisp import QuantumVariable, h, measure
from qrisp.jasp import q_cond
from tests import support


def qrisp_program():
    register = QuantumVariable(2)
    h(register[0])
    condition = measure(register[0])

    def measure_second(data):
        measure(data[1])
        return data

    def leave_unchanged(data):
        return data

    register = q_cond(condition, measure_second, leave_unchanged, register)
    return condition


class ConditionalMeasurementTest(support.ValidationTest):
    case_dir = Path(__file__).parent

    def test_conversion_and_validation(self) -> None:
        super().test_conversion_and_validation()
        for mode in ("static", "dynamic"):
            support.require_adjacent(
                support.output(self.case_dir, mode).read_text(),
                "call void @__quantum__qis__mz__body",
                "call void @__quantum__rt__result_record_output",
                2,
            )
        dynamic = support.output(self.case_dir, "dynamic").read_text()
        self.assertEqual(dynamic.count("call ptr @__quantum__rt__result_allocate(ptr null)"), 2)
        self.assertEqual(dynamic.count("  call void @__quantum__rt__result_release"), 2)
        before_branch, after_branch = dynamic.split("br i1", 1)
        self.assertEqual(before_branch.count("call ptr @__quantum__rt__result_allocate"), 2)
        self.assertEqual(after_branch.count("call void @__quantum__rt__result_release"), 2)
