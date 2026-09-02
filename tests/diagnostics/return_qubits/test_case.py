import unittest
from pathlib import Path

from tests import support


class ReturnQubitsTest(unittest.TestCase):
    def test_rejects_dynamic_array_escape(self) -> None:
        support.expect_conversion_failure(
            support.fixture(Path(__file__).parent),
            "dynamic QIR cannot return qubits backed by stack storage",
            support.temp_dir(),
            mode="dynamic",
        )
