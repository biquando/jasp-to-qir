# AGENTS.md

## Project

This repository converts Jasp MLIR into QIR 2.1 for the Adaptive Profile. Keep
changes focused on preserving program semantics and producing validator-compliant
QIR.

## References
- Jasp MLIR: https://qrisp.eu/reference/Jasp/MLIR%20Interface.html#jasp-dialect-specification
- QIR Base profile: https://github.com/qir-alliance/qir-spec/blob/2.1/specification/profiles/Base_Profile.md
- QIR Adaptive profile: https://github.com/qir-alliance/qir-spec/blob/2.1/specification/profiles/Adaptive_Profile.md
- Quantinuum QIR reference: https://github.com/Quantinuum/qir-qis/blob/main/qtm-qir-reference.md

## Pipeline layout

- `include/JaspToQIR/Dialect/Jasp/IR/JaspDialect.td` and `JaspOps.td` are the
  vendored Qrisp TableGen dialect definitions. CMake generates the C++ dialect
  at build time; do not add a build-time or runtime dependency on a `Qrisp/`
  checkout.
- Read `lib/README.md` for details about the lowering passes.
- `tools/jasp-to-qir.cpp` registers the generated dialect, the custom pass,
  and standard MLIR passes for `mlir-opt`.
- `tools/jasp_to_qir.py` runs the full pipeline, invokes `mlir-translate`, and
  replaces translator metadata with the required QIR module flags.
- `tools/validate_qir.py` validates emitted QIR.
- `tools/qrisp_statevector.py` emits normalized state-vector JSON from an
  unmeasured Qrisp source program; `tools/qir_statevector.py` emits the same
  format by running QIR with Selene/QuEST.
- `tests/run_tests.py` discovers the categorized `unittest` suite, while
  `tests/support.py` owns shared conversion, validation, simulation, caching,
  and reporting mechanics. `tests/generate_qrisp_fixtures.py` regenerates the
  colocated `input.mlir` for every case that declares `qrisp_program`.

## Common commands

Build with Homebrew LLVM/MLIR:

```sh
cmake -S . -B build -DMLIR_DIR=/opt/homebrew/opt/llvm@21/lib/cmake/mlir
cmake --build build -j
```

Convert and validate one input:

```sh
python3 tools/jasp_to_qir.py input.mlir output.ll
./venv/bin/python tools/validate_qir.py output.ll
```

Set `LLVM_BIN` if LLVM 21 is not on `PATH`. Run all regressions with:

```sh
./venv/bin/python tests/run_tests.py
```

Use `run_qir.py` to run a QIR file.
```sh
python tools/run_qir.py <.ll file> <num_qubits>
```

## Implementation conventions

- Inputs must be syntactically valid MLIR. Parse Qrisp's custom Jasp assembly
  through the generated dialect; do not reintroduce text/regex normalization.
- Do not statically unroll `scf` or `cf` control flow. Keep it in MLIR and use
  the standard SCF-to-CF and LLVM lowering passes so branches and loops remain
  branches and loops in emitted QIR.
- Keep custom lowering limited to Jasp semantics and rank-zero scalar wrapper
  elimination. Prefer standard MLIR patterns and lowering passes for functions,
  control flow, arithmetic, and LLVM conversion.
- QIR ABI details matter: use supported QIS/runtime declarations, required
  module flags, entry-point attributes, and correct function attributes for
  irreversible measurement operations.
- Dynamic resource management is the driver default and uses consecutive QIR
  resource handles. Static mode is selected with
  `--resource-management static` and uses the Adaptive Profile's optional
  qubit/result allocation and array APIs.
- Dynamic `jasp.create_qubits` creates a runtime-sized stack buffer and fills it
  in an SCF loop with calls to `__quantum__rt__qubit_allocate`. Explicit
  `jasp.delete_qubits` releases each referenced qubit in a loop, while undeleted
  allocations remain live until runtime teardown. Allocation calls receive a
  null error pointer and terminate on failure.
- Dynamic measurements share one reusable, compile-time-sized result buffer
  allocated in the QIR entry point's entry block and released at every entry
  point return. Helpers access it through a private pointer global. The driver
  default is 64 slots and can be changed with `--result-buffer-size`. Scalar
  measurements record a result value;
  qubit-array measurements pack least-significant-bit first into an `i64` and
  record one integer output.
- Dynamic qubit-array sizes may be runtime values. Returning a qubit or qubit
  array from an emitted helper function is rejected because its backing stack
  storage cannot escape. Source-level returns from `main` are discarded during
  entry-point preparation and therefore do not escape.
- Dynamic `jasp.slice` creates a view with Python-style normalized indices.
  Dynamic `jasp.fuse` copies scalar qubits and/or array elements into a new
  runtime-sized stack buffer. The source Jasp program remains responsible for
  correct ownership and nonduplicating deletion. Static slicing is supported,
  but fusion requires dynamic resource management.
- Record a measurement result immediately after its corresponding `mz` call;
  do not defer output recording to function exit. Output labels use the
  `result_<n>` form.
- Lower Jasp `cx` to QIR `cnot`. Lower array reset through SCF so standard
  SCF-to-CF conversion preserves source control flow instead of unrolling it.
- Unsupported quantum gates should produce a clear conversion error rather
  than silently generating different behavior.
- Dialect operations that are parsed but not yet assigned Adaptive-Profile QIR
  semantics (`parity`) must produce a clear conversion error rather than
  silently generating different behavior.

## Tests and fixtures

- Group tests by purpose under `tests/validation/`, `tests/statevector/`,
  `tests/semantics/`, `tests/diagnostics/`, or `tests/generation/`. Each program
  case owns a directory containing `test_case.py` and `input.mlir`.
- Add or modify a Qrisp-based case's `qrisp_program` in its `test_case.py`, then
  regenerate its colocated checked-in `input.mlir` with
  `tests/generate_qrisp_fixtures.py`. Fixture freshness is checked in isolated
  cache and temporary directories.
- Put shared test mechanics in `tests/support.py`, but keep case-specific
  assertions and expected diagnostics in the owning `test_case.py`.
- State-vector equivalence fixtures must not measure or reset. Return their
  live quantum values so Qrisp and Selene/QuEST can compare normalized dense
  vectors in both static and dynamic modes. Pass the simulator qubit capacity
  to `support.verify_statevector_case` from the case's test method.
- Measurement equivalence fixtures may use reset, mid-circuit measurement, and
  measurement-controlled gates, but every explicit measurement outcome must be
  deterministic and represented in the returned value. Pass result widths and
  an independently known expected bitstring to
  `support.verify_measurement_case`; QubitArray integers expand
  least-significant-bit first.
- The semantic suite uses `selene-sim`/QuEST for QIR execution because
  qir-runner does not link the dynamic array runtime APIs. Cross-simulator
  state vectors are compared after global-phase normalization with a `1e-6`
  tolerance. Do not weaken the tolerance or make semantic checks optional
  without a demonstrated numerical need.
- A successful run writes the ignored human-readable report
  `tests/results/semantic_results.txt`, containing Qrisp, static-QIR, and
  dynamic-QIR amplitudes or bitstrings side by side. Do not move retained Selene
  build artifacts out of `tests/.tmp/`.
- Run the full test script after pipeline changes.
