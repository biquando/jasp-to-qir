"""Qrisp backend execution, including classical wiring and library QAOA."""

import unittest

import networkx as nx
import numpy as np
from qrisp import QuantumCircuit, QuantumVariable
from qrisp.qaoa import maxcut_problem

from tools.qir_backend import QIRBackend, circuit_mlir


class QIRBackendTest(unittest.TestCase):
    def test_measurement_wiring(self):
        circuit = QuantumCircuit(3, 3)
        circuit.x(0)
        circuit.measure(0, 2)
        circuit.measure(2, 0)
        # c1 is unassigned; c2 receives q0 rather than q2.
        self.assertEqual(dict(QIRBackend().run(circuit, shots=8)), {"100": 8})

    def test_bound_angles_and_composite_gate(self):
        pair = QuantumCircuit(2)
        pair.rx(np.pi, 0)
        pair.cx(0, 1)
        circuit = QuantumCircuit(2, 2)
        circuit.append(pair.to_gate(), [0, 1])
        circuit.measure(0, 0)
        circuit.measure(1, 1)
        job = QIRBackend().run_async([circuit], shots=8)
        self.assertTrue(job.done())
        self.assertEqual(job.result().all_counts, [{"11": 8}])

    def test_qrisp_qaoa(self):
        problem = maxcut_problem(nx.Graph([(0, 1)]))
        # These depth-one angles cut a single edge with probability one.
        results = problem.run(
            QuantumVariable(2), depth=1, max_iter=4,
            init_point=np.array([np.pi / 4, -np.pi / 8]),
            mes_kwargs={"backend": QIRBackend(), "shots": 32},
        )
        self.assertTrue(set(results) <= {"01", "10"})
        self.assertAlmostEqual(problem.cl_cost_function(results), -1)

    def test_rejects_feedback(self):
        circuit = QuantumCircuit(1, 1)
        circuit.measure(0, 0)
        circuit.x(0)
        with self.assertRaisesRegex(ValueError, "terminal measurements"):
            circuit_mlir(circuit)


if __name__ == "__main__":
    unittest.main()
