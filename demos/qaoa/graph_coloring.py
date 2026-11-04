"""Run from the repository root: python -m qaoa.graph_coloring"""

import networkx as nx
from qrisp import QuantumArray
from qrisp.qaoa import QuantumColor, graph_coloring_problem

from tools.qir_backend import QIRBackend


if __name__ == "__main__":
    graph = nx.path_graph(3)
    colors = ["red", "blue"]
    problem = graph_coloring_problem(graph)
    problem.set_init_function(lambda q: q.encode(["red", "blue", "red"]))
    results = problem.run(
        QuantumArray(qtype=QuantumColor(colors), shape=len(graph)),
        depth=1, max_iter=20,
        mes_kwargs={"backend": QIRBackend(), "shots": 256},
    )
    print("Expected coloring cost:", problem.cl_cost_function(results))
    print(dict(results))
