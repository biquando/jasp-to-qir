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

- `include/Jasp/IR/JaspDialect.td` and `JaspOps.td` are the vendored Qrisp
  TableGen dialect definitions. CMake generates the C++ dialect at build time;
  do not add a build-time or runtime dependency on a `Qrisp/` checkout.
- `lib/JaspOps.cpp` registers the generated dialect and implements its local
  semantic verifiers.
- `lib/JaspToQIR.cpp` contains the typed Jasp lowering and rank-zero tensor
  scalarization. It uses standard Func and SCF type-conversion patterns so
  Jasp values can flow through calls and structured control flow.
- `tools/jasp-to-qir.cpp` registers the generated dialect, the custom pass,
  and standard MLIR passes for `mlir-opt`.
- `tools/jasp_to_ll.py` runs the full pipeline, emits LLVM IR, and adds required
  QIR declarations, module flags, entry-point attributes, and result recording.
- `tools/validate_qir.py` validates emitted QIR.
- `tools/qrisp_statevector.py` emits normalized state-vector JSON from an
  unmeasured Qrisp source program; `tools/qir_statevector.py` emits the same
  format by running QIR with Selene/QuEST.
- `tests/generate_qrisp_fixtures.py` generates Jasp fixtures with Qrisp;
  `tests/run_tests.py` regenerates them, runs structural regressions, and
  compares Qrisp behavior with static and dynamic QIR.

## Common commands

Build with Homebrew LLVM/MLIR:

```sh
cmake -S . -B build \
  -DMLIR_DIR=/opt/homebrew/opt/llvm/lib/cmake/mlir \
  -DLLVM_DIR=/opt/homebrew/opt/llvm/lib/cmake/llvm
cmake --build build -j
```

Convert and validate one input:

```sh
python3 tools/jasp_to_ll.py input.mlir output.ll
./venv/bin/python tools/validate_qir.py output.ll
```

Set `LLVM_BIN` if LLVM tools are not on `PATH`. Run all regressions with:

```sh
./venv/bin/python tests/run_tests.py
```

Use qir-runner to run a QIR file.
```sh
./venv/bin/qir-runner -f <QIR file> -s <shots>
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
  irreversible measurement and reset operations.
- Static resource management is the driver default and uses consecutive QIR
  resource handles. Dynamic mode is selected with
  `--resource-management dynamic` and uses the Adaptive Profile's optional
  qubit/result allocation and array APIs.
- Dynamic `jasp.create_qubits` uses fixed-size classical pointer storage with
  `__quantum__rt__qubit_array_allocate`; explicit `jasp.delete_qubits` emits
  the matching release, while undeleted allocations remain live until runtime
  teardown. Allocation calls receive a null error pointer and terminate on
  failure.
- Scalar measurements dynamically allocate and record one result. Qubit-array
  measurements use result arrays and one array output record while retaining
  Jasp's packed integer for classical control flow. Qubit-array sizes must be
  compile-time constants in both modes because the targeted Quantinuum ABI
  requires fixed-size classical pointer buffers.
- Record a measurement result immediately after its corresponding `mz` call;
  do not defer output recording to function exit. Output labels use the
  `result_<n>` form.
- Lower Jasp `cx` to QIR `cnot`. Lower array reset through SCF so standard
  SCF-to-CF conversion preserves source control flow instead of unrolling it.
- Unsupported quantum gates should produce a clear conversion error rather
  than silently generating different behavior.
- Dialect operations that are parsed but not yet assigned Adaptive-Profile QIR
  semantics (`slice`, `fuse`, and `parity`) must produce clear conversion
  errors rather than silently generating different behavior.

## Tests and fixtures

- Add or modify Qrisp-based coverage in `tests/generate_qrisp_fixtures.py`,
  then regenerate the checked-in fixtures under `tests/fixtures/qrisp/`. The
  test runner regenerates into `tests/.tmp/` with isolated cache directories
  and fails if checked-in fixtures are stale.
- Add regression checks to `tests/run_tests.py` for every semantic bug fixed,
  including expected failures for unsupported operations.
- State-vector equivalence fixtures must not measure or reset. Return their
  live quantum values so Qrisp and Selene/QuEST can compare normalized dense
  vectors in both static and dynamic modes. Register them in
  `STATEVECTOR_CASES` with the simulator qubit capacity.
- Measurement equivalence fixtures may use reset, mid-circuit measurement, and
  measurement-controlled gates, but every explicit measurement outcome must be
  deterministic and represented in the returned value. Register result widths
  and an independently known expected bitstring in `MEASUREMENT_CASES`;
  QubitArray integers expand least-significant-bit first.
- The semantic suite uses `selene-sim`/QuEST for QIR execution because
  qir-runner does not link the dynamic array runtime APIs. Cross-simulator
  state vectors are compared after global-phase normalization with a `1e-6`
  tolerance. Do not weaken the tolerance or make semantic checks optional
  without a demonstrated numerical need.
- A successful run writes the ignored human-readable report
  `tests/results/semantic_results.txt`, containing Qrisp, static-QIR, and
  dynamic-QIR amplitudes or bitstrings side by side. Do not move retained Selene
  build artifacts out of `tests/.tmp/`.
- Run the full test script after pipeline changes. It validates each generated
  `.ll` file and also checks the intermediate-file option. With
  `--keep-intermediates`, the driver retains only `.llvm.mlir` and `.raw.ll`;
  the removed generic and post-Jasp stages are no longer emitted.
