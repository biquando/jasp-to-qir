# `jasp-to-qir` Pipeline Architecture

`jasp-to-qir` is an `mlir-opt`-based lowering pipeline for converting
Qrisp/Jasp-generated MLIR code to QIR. This document gives an outline of the
pipeline. The detailed descriptions of each custom lowering pass are in:

- [`Conversion/LowerJaspToQIR/README.md`](Conversion/LowerJaspToQIR/README.md)
- [`Transforms/FinalizeQIRLLVM/README.md`](Transforms/FinalizeQIRLLVM/README.md)

## Lowering passes

```text
Qrisp/Jasp-generated MLIR with StableHLO already lowered to scf/math/arith/tensor
  |
  | --lower-jasp-to-qir (lib/Conversion/LowerJaspToQIR)
  v
LLVM-dialect QIR calls mixed with func/scf/math/arith
  |
  | --canonicalize
  | --inline
  v
Inlined MLIR functions
  |
  | --canonicalize
  | --symbol-dce
  | --convert-scf-to-cf
  | --convert-cf-to-llvm
  | --convert-math-to-llvm
  | --convert-arith-to-llvm
  | --convert-func-to-llvm
  | --reconcile-unrealized-casts
  v
LLVM-dialect only
  |
  | --finalize-qir-llvm (lib/Transforms/FinalizeQIRLLVM)
  v
QIR-compliant LLVM-dialect module (ready for mlir-translate)
```

There are four stages to the pipeline:
1. Jasp's `jaspr.to_mlir(lower_stablehlo=True)` gives MLIR code that contains
   the custom Jasp dialect, as well as func/scf/math/arith/tensor dialects. The
   first custom pass (`--lower-jasp-to-qir`) converts the Jasp-dialect
   operations/types to LLVM-dialect, matching the QIR spec.
2. Quantinuum has an undocumented restriction: qubits cannot be allocated inside
   helper functions. To get around this, we inline all functions on the MLIR
   level.
3. We lower func/scf/math/arith down to LLVM-dialect to prepare for QIR output.
4. This is the second custom pass. We make some small modifications to the
   module in order to make it QIR-compliant (besides the module flags, which are
   added to the actual `.ll` file in post-processing).

## Source files

| Path | Description |
| ---- | ----------- |
| `tools/jasp_to_qir.py`                         | Python wrapper for the lowering pipeline. |
| `tools/jasp-to-qir.cpp`                        | Main module: registers passes and dialects. |
| `include/JaspToQIR/Conversion/LowerJaspToQIR`  | Public interface for the Jasp lowering pass. |
| `include/JaspToQIR/Transforms/FinalizeQIRLLVM` | Public interface for the QIR finalization pass. |
| `include/JaspToQIR/Dialect/Jasp/IR`            | Vendored TableGen definitions and public Jasp dialect header. |
| `lib/Dialect/Jasp/IR`                          | Registers the generated Jasp operations and types. |
| `lib/Conversion/LowerJaspToQIR`                | Contains the `--lower-jasp-to-qir` pass. |
| `lib/Transforms/FinalizeQIRLLVM`               | Contains the `--finalize-qir-llvm` pass. |

## Jasp dialect registration

The Jasp dialect definitions come from Qrisp's provided TableGen files. The
component CMake file generates the operation/type definitions from the TableGen
files, which are then linked through `lib/Dialect/Jasp/IR/JaspOps.cpp`.

See [Jasp Documentation](https://qrisp.eu/reference/Jasp/MLIR%20Interface.html#jasp-dialect-specification)
for the full dialect specification.
