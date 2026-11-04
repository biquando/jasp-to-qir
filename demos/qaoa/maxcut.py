"""Run from the repository root: python -m qaoa.maxcut"""

import networkx as nx
from qrisp import QuantumVariable
from qrisp.qaoa import maxcut_problem

from tools.qir_backend import QIRBackend


if __name__ == "__main__":
    graph = nx.path_graph(3)
    problem = maxcut_problem(graph)
    results = problem.run(
        QuantumVariable(len(graph)), depth=1, max_iter=20,
        mes_kwargs={"backend": QIRBackend(), "shots": 256},
    )
    print("Expected cut:", -problem.cl_cost_function(results))
    print(dict(results))
