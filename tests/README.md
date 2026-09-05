# Tests

The suite uses standard-library `unittest`. There is no registry or custom test
configuration language. `support.py` contains conversion, simulator comparison,
and temporary-directory helpers. `run_tests.py` adds cache isolation and the
semantic report to the standard `unittest` command line.

Build the converter first and use the repository virtual environment. Select
LLVM **21** explicitly if another version is on `PATH`; newer LLVM textual IR
may not be readable by the installed QIR validator:

```sh
export LLVM_BIN=/opt/homebrew/opt/llvm@21/bin
./venv/bin/python tests/run_tests.py
```

The runner works from any working directory when invoked by its absolute path.
It accepts ordinary unittest arguments:

```sh
# One case
./venv/bin/python tests/run_tests.py tests.semantics.feedback.test_case
# One category
./venv/bin/python tests/run_tests.py discover -s tests/validation -t .
# Matching tests; stop at the first failure
./venv/bin/python tests/run_tests.py discover -s tests -t . -k measurement -f
# Fast harness checks (no Qrisp, LLVM, or Selene needed)
./venv/bin/python tests/run_tests.py discover -s tests/harness -t .
```

Missing dependencies and simulator failures are errors, never silent skips.
Selene needs permission to open a local socket. Each conversion has its own
working directory under `tests/.tmp/`; the runner cleans up and restores cache
environment variables after the run. Results are written to
`tests/results/semantic_results.txt`, with Qrisp and QIR values side by side.
A failed run marks the report partial. Running with `python -m unittest` also
works, but use the runner for report writing and explicit session cleanup.

## Adding a test

Choose the smallest test that establishes the behavior:

- `validation/`: conversion plus QIR validation and LLVM verification.
- `statevector/`: unmeasured program equivalence with Qrisp and Selene/QuEST.
- `semantics/`: deterministic measurement outcomes, including reset and feedback.
- `diagnostics/`: unsupported inputs and their relevant error messages.
- `generation/`: checked-in Qrisp fixture freshness.
- `harness/`: focused checks that the comparison helpers reject incorrect data.

For a program case, create a directory with `__init__.py`, `test_case.py`, and
`input.mlir`. New categories also need `__init__.py`. Nothing needs registering.
A validation-only test is just:

```python
from pathlib import Path
from tests import support

class MyFeatureTest(support.ValidationTest):
    case_dir = Path(__file__).parent
```

This validates both resource modes as independent subtests. For a dynamic-only
case, use an ordinary `unittest.TestCase` and call
`support.output(Path(__file__).parent, "dynamic")`.

For Qrisp-generated input, define `qrisp_program()` in `test_case.py` and generate
its fixture (case paths are relative to `tests/`):

```sh
./venv/bin/python tests/generate_qrisp_fixtures.py semantics/my_case
# Or regenerate all cases
./venv/bin/python tests/generate_qrisp_fixtures.py
```

Edit the source function, then regenerate; do not hand-edit generated MLIR.
The freshness test regenerates in isolation and checks exact bytes. A Qrisp
upgrade can require fixture regeneration; changes to our lowering pipeline do
not. Keep Qrisp imports in each case, not in the harness.

For semantic tests, use an ordinary `unittest.TestCase` with one helper call:

```python
# No measurement or reset; qrisp_program must return its live quantum values.
support.verify_statevector_case(Path(__file__).parent, qubits=3)

# Every measurement must be deterministic and returned in execution order.
support.verify_measurement_case(
    Path(__file__).parent, qrisp_program,
    qubits=3, widths=(1, 2), expected=(1, 0, 1),
)
```

`qubits` is the simulator capacity, including temporary qubits. State vectors
are compared up to global phase with absolute tolerance `1e-6`. Unused trailing
qubits must be zero before they can be removed. Both resource modes run by
default; select `resource_modes=("dynamic",)` only for a feature that requires it.

Measurement `widths` describe the returned scalar/array leaves. An array integer
expands least-significant-bit first. `expected` must be independently known,
not copied from the converter's output. See `semantics/conditional_output` and
`semantics/measurement_loop` for conditional output and repeated measurements.

Prefer validator acceptance and observable behavior over generated-text checks.
Do not assert SSA names, helper inlining, allocation counts, instruction
adjacency, attribute numbering, or intermediate filenames. A text assertion is
appropriate only when the spelling itself is the contract, such as a requested
runtime buffer capacity. Keep option-specific checks in their own tests so a
change affects the test that owns that option.

`semantics/lcu_rus` wraps Qrisp's `inner_LCU` in its `RUS` decorator, with
explicit herald reset/deletion to keep retries bounded in live qubit usage.
It covers random internal heralds and a deterministic final answer: `(I + X)|1>` prepares `|+>`, measured as zero after
a Hadamard. It uses a case-local check instead of the deterministic-trace
helper: every QIR trace must contain failed heralds, then one successful herald,
then the known output (zero failed heralds is valid). Retry counts need not match
Qrisp or a saved random sequence. Sixteen shots are checked in dynamic mode,
which is required by the generated runtime-sized allocations; the shared
harness needs no stochastic-comparison options.
