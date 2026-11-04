# Magnetization with Trotter evolution

Run both models from the repository root:

```sh
MPLBACKEND=Agg LLVM_BIN=/opt/homebrew/opt/llvm@21/bin ./venv/bin/python -m demos.magnetization_trotter.magnetization
```

This matches the physical benchmark in `demos/magnetization_lcu`: two spins,
`J = B = 1`, and nine times from 0 to 3.2. TFIM starts in the all-zero state
and measures average Z magnetization. Heisenberg starts in the same alternating
Ry product state and measures both average and staggered X magnetization.
The two Heisenberg observables use the same measurement shots.

The Trotter algorithm retains ten first-order steps and 250 shots per time
point. These are algorithm and sampling settings, not matched resource budgets:
LCU uses Taylor approximation and its separately tuned attempt counts.
Each model is one program that measures and resets its register between time
points, so a single program shot returns nine independent-time measurements.

The script compiles and validates `tfim.ll` and `heis.ll`, simulates them locally,
and estimates the HQC cost including the fixed charge for each model's program.
It saves `magnetization_tfim.png` and `magnetization_heis.png` with exact reference
curves and one-standard-error bars. `benchmark_results.json` records the
parameters, estimated costs, means, errors, exact values, and observed RMSE.
HQC values are local estimates, not hardware bills or guaranteed upper bounds.

The complete previous demo was backed up, with file checksums verified, to
`../magnetization_trotter_backup_2026_10_12/` before any edits. That snapshot
retains the ten-spin, `B=3`, 30-time-point benchmark and its plots. LCU's cost
tuner imports that snapshot to preserve its historical budget reference.
The existing `magnetization_nexus.*` data/plotting script and `magnetization*.mlir`
files in this directory are also legacy ten-spin artifacts; the current runner
uses the model-specific `tfim` and `heis` output names instead.
