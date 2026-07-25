# Jasp to QIR

This project converts the Jasp MLIR syntax documented by
[Qrisp](https://qrisp.eu/reference/Jasp/MLIR%20Interface.html#jasp-dialect-specification)
to QIR 2.1 LLVM IR for the Adaptive Profile.

## Pipeline

The conversion has two stages:

1. `build/jasp-to-qir` parses the generated Jasp dialect, verifies and lowers
   typed Jasp operations, scalarizes Qrisp's rank-zero tensor wrappers, and
   runs MLIR's standard SCF, CF, arith, and func conversions. The checked-in
   TableGen definitions under `include/Jasp/IR` are derived from Qrisp and do
   not require a Qrisp checkout at build or runtime.
2. `tools/jasp_to_ll.py` translates the resulting LLVM dialect to LLVM IR and
   renders the QIR declarations, entry-point instrumentation, result records,
   and profile metadata that MLIR cannot represent.

The final QIR uses standard `__quantum__qis__*__body` calls, output-recording
runtime calls, entry-point attributes, and QIR module flags. Controlled-X is
mapped from Jasp `cx` to QIR `cnot`. Resource management can be selected at
conversion time: static mode uses consecutive QIR resource IDs, while dynamic
mode uses the optional Adaptive Profile allocation and array APIs.

Measurement results are recorded immediately after the measurement executes,
so measurements in untaken control-flow branches are not emitted as outputs.
Resetting a qubit array is lowered to an SCF loop and then follows the same
standard SCF-to-CF-to-LLVM lowering as source control flow.

## Build

```sh
cmake -S . -B build \
  -DMLIR_DIR=/opt/homebrew/opt/llvm/lib/cmake/mlir \
  -DLLVM_DIR=/opt/homebrew/opt/llvm/lib/cmake/llvm
cmake --build build -j

python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Convert

```sh
python3 tools/jasp_to_ll.py input.mlir output.ll
```

Static resource management is the default and preserves compatibility with
backends that do not implement the optional allocation APIs. Select dynamic
qubit/result management and arrays with:

```sh
python3 tools/jasp_to_ll.py --resource-management dynamic input.mlir output.ll
```

The underlying MLIR pass exposes the same choice as
`--lower-jasp-to-qir="resource-management=dynamic"`. In dynamic mode,
`jasp.create_qubits` uses a fixed-size LLVM pointer array and
`__quantum__rt__qubit_array_allocate`; an explicit `jasp.delete_qubits` emits
the matching release. Allocations without a Jasp delete remain live until
runtime teardown. Allocation failures terminate execution because the runtime
calls receive a null error pointer.

Scalar measurements dynamically allocate and record one result. Qubit-array
measurements allocate a result array and produce one array output record in
qubit order, while retaining Jasp's packed integer value for classical use.
Both modes currently require each Jasp qubit-array size to be a compile-time
constant because the targeted Quantinuum QIR implementation requires
fixed-size classical pointer buffers.

The scripts use `/opt/homebrew/opt/llvm/bin` by default. Set `LLVM_BIN` when
the LLVM tools are installed elsewhere:

```sh
LLVM_BIN=/path/to/llvm/bin python3 tools/jasp_to_ll.py input.mlir output.ll
```

Intermediates are removed by default. Keep them for inspection with:

```sh
python3 tools/jasp_to_ll.py --keep-intermediates input.mlir output.ll
```

When kept, the driver writes these files next to the output:

- `output.llvm.mlir`: standard CF/arith/func-to-LLVM output
- `output.raw.ll`: direct `mlir-translate` output before QIR profile metadata

Inputs must be syntactically valid MLIR; the generated dialect accepts Qrisp's
custom Jasp assembly directly.

## Validate

Install the validation dependency into `./venv` from `requirements.txt`, then
run:

```sh
./venv/bin/python tools/validate_qir.py output.ll
```

For additional LLVM structural checks:

```sh
/opt/homebrew/opt/llvm/bin/llvm-as output.ll -o /dev/null
/opt/homebrew/opt/llvm/bin/opt -passes=verify -disable-output output.ll
```

To run a generated QIR program, use qir-runner:
```sh
./venv/bin/qir-runner -f <QIR file> -s <shots>
```

## Test

Run the complete suite with:

```sh
./venv/bin/python tests/run_tests.py
```

The runner regenerates Qrisp fixtures into ignored `tests/.tmp/` storage,
compares them with the checked-in copies, converts every valid fixture in
static and dynamic resource modes, validates the resulting QIR, checks
expected failures, and runs semantic equivalence checks with Qrisp and
Selene/QuEST.

The semantic checks have two categories:

- State-vector tests contain no measurements or resets. The same Qrisp source
  program is simulated with Qrisp and converted to static and dynamic QIR,
  which Selene executes with the QuEST state-vector simulator. Dense amplitudes
  are compared after normalizing global phase, using a `1e-6` tolerance for
  Qrisp's single-precision gate kernels.
- Measurement tests may contain reset and measurement-controlled gates, but
  must have exactly one possible output bitstring. One Qrisp shot and one
  Selene shot for each resource mode must all equal the independently declared
  expected bitstring. Qubit-array results are compared least-significant-bit
  first, matching Qrisp's packed integer representation.

Successful semantic values are retained for visual inspection in
`tests/results/semantic_results.json`. For every computational basis state,
the report places the Qrisp, static-QIR, and dynamic-QIR amplitudes together
and records each mode's maximum absolute difference. Measurement entries show
the expected and three observed bitstrings side by side. The report is
regenerated on every suite run and ignored by Git.

Fixtures are organized by purpose:

- `tests/fixtures/qrisp/`: all valid fixtures, generated and checked in from
  their Qrisp programs.
- `tests/fixtures/invalid/`: expected conversion failures.

Regenerate the checked-in Qrisp fixtures with:

```sh
./venv/bin/python tests/generate_qrisp_fixtures.py
```

Use `--output-dir <path>` to generate them elsewhere. Intermediate QIR, fixture
generations, Selene builds, and caches remain under `tests/.tmp/`, and each
per-run directory is removed automatically. Only the ignored semantic report
under `tests/results/` is retained.

The standalone state-vector tools used by the suite can also be invoked
directly:

```sh
./venv/bin/python tools/qrisp_statevector.py program.py -o qrisp-state.json
./venv/bin/python tools/qir_statevector.py program.ll -o qir-state.json
```

Dynamic QIR does not declare a fixed capacity, so pass its simulator capacity
with `--n-qubits <count>` to `qir_statevector.py`.

Control flow is not matched or synthesized by the Python driver. Any SCF
operation supported by MLIR's standard SCF-to-CF conversion follows the same
pipeline; loops remain loops and conditionals become LLVM branches. Mid-circuit
measurements are emitted in place and read through `__quantum__rt__read_result`
when their values feed classical control flow.
