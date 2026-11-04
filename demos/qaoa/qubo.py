"""Run from the repository root: python -m qaoa.qubo"""

import numpy as np
from qrisp import QuantumVariable
from qrisp.qaoa import QUBO_problem

from tools.qir_backend import QIRBackend


if __name__ == "__main__":
    matrix = np.array([[1., 2., 0.], [0., -1., 1.], [0., 0., 1.]])
    problem = QUBO_problem(matrix)
    results = problem.run(
        QuantumVariable(len(matrix)), depth=1, max_iter=20,
        mes_kwargs={"backend": QIRBackend(), "shots": 256},
    )
    print("Expected QUBO cost:", problem.cl_cost_function(results))
    print(dict(results))
