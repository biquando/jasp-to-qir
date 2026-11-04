"""Run from the repository root: python -m qaoa.e3lin2"""

from qrisp import QuantumVariable
from qrisp.qaoa import e3lin2_problem

from tools.qir_backend import QIRBackend


if __name__ == "__main__":
    clauses = [[0, 1, 2, 1]]  # x0 + x1 + x2 = 1 (mod 2)
    problem = e3lin2_problem(clauses)
    results = problem.run(
        QuantumVariable(3), depth=1, max_iter=20,
        mes_kwargs={"backend": QIRBackend(), "shots": 256},
    )
    print("Expected satisfied equations:", -problem.cl_cost_function(results))
    print(dict(results))
