"""Run from the repository root: python -m qaoa.max_set_packing"""

from qrisp import QuantumVariable
from qrisp.qaoa import max_set_packing_problem

from tools.qir_backend import QIRBackend


if __name__ == "__main__":
    sets = [{0, 1}, {1, 2}, {2, 3}]
    problem = max_set_packing_problem(sets)
    results = problem.run(
        QuantumVariable(len(sets)), depth=1, max_iter=20,
        mes_kwargs={"backend": QIRBackend(), "shots": 256},
    )
    print("Expected packing size:", -problem.cl_cost_function(results))
    print(dict(results))
