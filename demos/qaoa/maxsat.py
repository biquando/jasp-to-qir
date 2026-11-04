"""Run from the repository root: python -m qaoa.maxsat"""

from qrisp import QuantumVariable
from qrisp.qaoa import maxsat_problem

from tools.qir_backend import QIRBackend


if __name__ == "__main__":
    formula = (3, [[1, -2], [2, 3]])  # (x1 OR NOT x2) AND (x2 OR x3)
    problem = maxsat_problem(formula)
    results = problem.run(
        QuantumVariable(formula[0]), depth=1, max_iter=20,
        mes_kwargs={"backend": QIRBackend(), "shots": 256},
    )
    print("Expected satisfied clauses:", -problem.cl_cost_function(results))
    print(dict(results))
