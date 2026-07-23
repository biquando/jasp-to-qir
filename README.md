# Jasp to QIR

This project converts the Jasp MLIR syntax documented by
[Qrisp](https://qrisp.eu/reference/Jasp/MLIR%20Interface.html#jasp-dialect-specification)
to QIR 2.1 LLVM IR for the Adaptive Profile.

## Pipeline

The conversion has three deliberately small stages:

1. `tools/jasp_to_generic.py` repairs arbitrary producer line wrapping,
   rewrites Jasp custom assembly into generic MLIR, scalarizes rank-0 tensors,
   and replaces Jasp-only handle types with LLVM-legal scalar types.
2. `build/jasp-to-qir`, built from `tools/jasp-to-qir.cpp` and
   `lib/JaspToQIR.cpp`, validates and lowers Jasp quantum operations, maps
   gates to QIR, and reports the static resources and profile capabilities
   required by the module.
3. `tools/jasp_to_ll.py` runs MLIR's standard `convert-scf-to-cf`,
   `convert-cf-to-llvm`, `convert-arith-to-llvm`, and `convert-func-to-llvm`
   passes, translates LLVM dialect to LLVM IR, and renders the QIR declarations,
   entry-point instrumentation, and metadata that MLIR cannot represent.

The final QIR uses standard `__quantum__qis__*__body` calls, output-recording
runtime calls, entry-point attributes, and QIR module flags. Controlled-X is
mapped from Jasp `cx` to QIR `cnot`.

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

- `output.generic.mlir`: generic, scalarized Jasp MLIR
- `output.qir.mlir`: Jasp operations lowered
- `output.llvm.mlir`: standard CF/arith/func-to-LLVM output
- `output.raw.ll`: direct `mlir-translate` output before QIR profile metadata

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

## Test

All test fixtures and their generated QIR files live in `tests/`. Run the
complete suite with:

```sh
./tests/run_tests.sh
```

Regenerate the Qrisp-produced MLIR fixtures with:

```sh
python tests/generate_qrisp_fixtures.py
```

The fixtures include:

- `tests/foo.mlir`: static allocation, H, and measurement
- `tests/bell.mlir`: H, CX/CNOT, and measurement
- `tests/tfim.mlir`: H, CX/CNOT, parameterized RZ, measurement, and a retained
  backwards-branching loop
- `tests/test.mlir`: multiple static qubit arrays and measurement-dependent
  adaptive branches
- `tests/qrisp_*.mlir`: fixtures generated directly by Qrisp

Expected conversion failures live under `tests/invalid/` and are checked by
the same test script.

Control flow is not matched or synthesized by the Python driver. Any SCF
operation supported by MLIR's standard SCF-to-CF conversion follows the same
pipeline; loops remain loops and conditionals become LLVM branches. Mid-circuit
measurements are emitted in place and read through `__quantum__rt__read_result`
when their values feed classical control flow.
