"""Run from the repository root: python -m qaoa.min_set_cover"""

from qrisp import QuantumVariable
from qrisp.qaoa import min_set_cover_problem

from tools.qir_backend import QIRBackend


if __name__ == "__main__":
    sets = [{0, 1}, {1, 2}, {0, 2}]
    problem = min_set_cover_problem(sets, set.union(*sets))
    results = problem.run(
        QuantumVariable(len(sets)), depth=1, max_iter=20,
        mes_kwargs={"backend": QIRBackend(), "shots": 256},
    )
    print("Expected cover cost:", problem.cl_cost_function(results))
    print(dict(results))
