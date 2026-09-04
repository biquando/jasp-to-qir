# FinalizeQIRLLVM Pass

This pass is a simple LLVM-dialect $\to$ LLVM-dialect MLIR transformation pass
that modifies the module to make it more QIR-compliant.

- **Input:** An MLIR program with only the LLVM dialect.
- **Output:** An MLIR program with only the LLVM dialect, with some applied
  transformations that make it QIR-compliant.

The following sections describe each of the transformations.

## Result buffer substitution

In the previous lowering pass, we outputted QIR that uses only a single result
buffer, shared among all measurements and outputs. The buffer is stack-allocated
only in the main function, so it we access it through a global alias.

After inlining, all uses of the result buffer are now in the main function, so
we no longer need the global alias. In fact, Quantinuum's validator will
complain if we use the alias when trying to output a result array.

Thus this transformation looks for all uses of the global alias and replaces
them with the original stack-allocated result buffer.

## Entrypoint attributes

In QIR, the module's entrypoint function needs some attributes:
 - `"entrypoint"`
 - `"qir_profiles"="adaptive_profile"`
 - `"output_labeling_schema"="labeled"`
If dynamic allocation is not supported, we also need these attributes:
 - `"required_num_qubits"=...`
 - `"required_num_results"=...`

## Declaration attributes

The following attributes should be added to function declarations:
- measurements require `irreversible`
- the result ptr argument of measurements requires `writeonly`
- the result ptr argument of `@__quantum__rt__read_result` requires `readonly`

## Entrypoint instrumentation

We insert `@__quantum__rt__initialize` at the start of the entrypoint function.

Although the Jasp dialect does have `create_quantum_kernel` and
`consume_quantum_kernel` that could be lowered by the lowering pass, these
functions are not actually emitted in practice. Thus we add the initialization
manually.
