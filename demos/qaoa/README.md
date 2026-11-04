# QAOA examples

These examples use Qrisp's QAOA optimizer with the prototype `QIRBackend` to run circuits locally through QIR. Each uses depth 1, up to 20 objective evaluations, and 256 shots per circuit. The binary examples use three problem qubits; coloring uses six, with two one-hot color qubits per node. The compiled circuit may also include ancillas, which are included in the simulator capacity. Sampling and optimization are stochastic, so the output is a demonstration and is not guaranteed to be optimal.

| Example | Problem |
| --- | --- |
| `maxcut` | Maximum cut on a three-node path |
| `max_independent_set` | Maximum independent set on a three-node path |
| `max_clique` | Maximum clique on a three-node path |
| `maxsat` | Two clauses over three variables |
| `qubo` | A three-variable quadratic unconstrained binary optimization problem |
| `e3lin2` | One parity equation over three variables |
| `max_set_packing` | Choose disjoint sets from three candidates |
| `min_set_cover` | Cover a three-element universe with three candidate sets |
| `graph_coloring` | Two-color a three-node path using `QuantumArray` and `QuantumColor` |

For the set problems, bit `i` selects set `i`; graph bitstrings put node 0 first. Coloring results decode directly to arrays of color names. Qrisp's coloring cost is the negative expectation of `4 ** (number of properly colored edges)`.

From the repository root, build the converter and run any example with the project's dependencies installed in `venv`. If LLVM 21 is not on your `PATH`, set `LLVM_BIN` to its binary directory; the example below uses the Homebrew location:

```sh
cmake -S . -B build -DMLIR_DIR=/opt/homebrew/opt/llvm@21/lib/cmake/mlir
cmake --build build -j
export LLVM_BIN=/opt/homebrew/opt/llvm@21/bin

python -m demos.qaoa.maxcut
python -m demos.qaoa.max_independent_set
python -m demos.qaoa.max_clique
python -m demos.qaoa.maxsat
python -m demos.qaoa.qubo
python -m demos.qaoa.e3lin2
python -m demos.qaoa.max_set_packing
python -m demos.qaoa.min_set_cover
python -m demos.qaoa.graph_coloring
```

## How it works

Qrisp's Python optimizer and classical cost function construct and evaluate circuits with bound numerical parameters. The backend transpiles each static `QuantumCircuit`, replays it into Jasp, converts the resulting MLIR to QIR, and runs it locally with Selene/QuEST. It turns the measured outputs into classical bit counts for Qrisp to decode and use in the optimization. Each submitted circuit is compiled again using temporary conversion files; execution is synchronous and returns a completed job. This backend does not execute on hardware.

## Scope

The backend requires measurements at the end of the circuit and numerical parameter values. Gates must transpile into operations supported by the Jasp-to-QIR compiler; quantum-controlled gates can work when they decompose into supported operations. Allocation, deallocation, and barrier metadata (`qb_alloc`, `qb_dealloc`, and `barrier`) are ignored during replay.

Classical feedback and gates after a measurement are rejected, and reset is unsupported by this replay path. Qrisp's Jasp `sample` and `jaspify` paths do not route through this backend. It provides finite-shot sampling, not analytic probabilities; `shots=None` uses the backend's default of 1,000 shots. These examples do not establish support for arbitrary Qrisp programs or problem instances.
