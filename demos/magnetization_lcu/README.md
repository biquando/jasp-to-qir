# Magnetization with Taylor LCU

Run from the repository root:

```sh
LLVM_BIN=/opt/homebrew/opt/llvm@21/bin ./venv/bin/python -m demos.magnetization_lcu.magnetization
```

Set `MPLBACKEND=Agg` to save the plots without opening a window.

The defaults are two spins, `J = B = 1`, nine times from 0 to 3.2, and 100
Taylor segments. The longer window shows oscillations while retaining the
original HQC budgets. The models use open chains:

- TFIM: `H = -J sum Z_i Z_(i+1) - B sum X_i`, starting in the all-zero
  state and measuring average Z magnetization.
- Heisenberg: `H = -J sum (X_i X_(i+1) + Y_i Y_(i+1) + Z_i Z_(i+1))
  - B sum Z_i`, starting in the alternating Ry product state and measuring
  both average and staggered X magnetization.

For two spins the Heisenberg observables are `(X_0 + X_1)/2` and
`(X_0 - X_1)/2`. Both are calculated from the same X-basis measurements;
staggered magnetization requires no additional quantum shots or gates.
Unlike total magnetization, the staggered observable responds to the exchange
interaction. Its larger signal makes the dynamics easier to see.
Packed QIR results put qubit zero in the least-significant bit.

## Approximation and circuit

Each time point divides time into `steps` segments of length `dt = t / steps`
and approximates evolution by `A(t) = (I - i*dt*H - dt**2*H**2/2)**steps`.
Each segment is second-order Taylor; this does not split the Hamiltonian into
Trotter factors. `QubitOperator` multiplies the segment polynomials and combines
like Pauli terms classically. The resulting operator is applied with a single
LCU call using Qrisp's `inner_LCU`.
Each complex coefficient is split into a positive magnitude for coefficient
state preparation and a phase carried by its Pauli unitary. Calling
`A.unitaries()` directly would hermitize the operator and discard its
imaginary contribution.

The combined operator has six Pauli terms at the nonzero times in this demo.
Increasing time or the segment count therefore need not increase circuit
depth here, although the coefficients and acceptance probabilities change.
Reducing `steps` does not buy a proportional increase in affordable shots.
The Pauli expansion can grow rapidly for larger systems; this classical
combination is not a scalable substitute for executing separate segments.

Without amplification, successful LCU prepares `A(t)|psi> / ||A(t)|psi>||`.
Each circuit returns a success flag and the system measurement; analysis keeps
only successful shots. Rejected attempts still count toward HQC cost. The
selector is reset and deleted after measurement. Qrisp's `prepare` builds the
coefficient state, and each Pauli term's `unitary()` supplies its gates.

One oblivious amplification round changes the successful block from
`B=A/sum(abs(coefficients))` to `3B - 4BB†B`. Both tuning and the plotted ideal
LCU markers include the resulting change in the conditional observable means.

## Cost-matched settings

The budgets remain those of the original ten-spin Trotter demo: `J=1`, `B=3`,
30 times from 0 to 2.9, ten first-order Trotter steps, and 250 shots. They are
3,697.50 HQC for TFIM and 10,987.50 HQC for Heisenberg. The physical system sizes,
fields, and time grids differ; this matches total budgets, not physical tasks.
The tuner imports `../magnetization_trotter_backup_2026_10_12/magnetization.py`
for this historical baseline. The active Trotter demo now matches LCU's two-spin
physical benchmark and reports its own, smaller cost independently.

The regenerated study selects:

| Model | Allocated HQC | Predicted average RMSE | Predicted staggered RMSE |
|---|---:|---:|---:|
| TFIM | 3,695.38 | 0.0231 | — |
| Heisenberg | 10,985.13 | 0.0123 | 0.0134 |

The tuner prices zero and one amplification round at each nonzero time,
then enumerates all 256 combinations. For each combination it allocates shots
and scores predicted **bias squared plus sampling variance**, equally weighted
across time points and plotted observables. The Heisenberg objective includes
both average and staggered magnetization; covariance is unnecessary for the
sum of their individual mean squared errors.

For each point, let `v` be the mean conditional variance across its observables,
`p` the acceptance probability, and `c` the HQC cost per attempted shot.
Allocation uses `shots proportional to sqrt(v/(p*c))`, followed by integer
rounding and a minimum of two attempts. The deterministic TFIM point at zero
time needs only two verification shots. The optimizer searches the tested
amplification combinations with this allocation rule; it does not claim global
optimality over circuits or every possible integer shot allocation.

Regenerate the cost/accuracy study with:

```sh
LLVM_BIN=/opt/homebrew/opt/llvm@21/bin ./venv/bin/python -m demos.magnetization_lcu.tune_cost
```

This writes `cost_study.json` and prints the shot and amplification lists.
Update the demo's `shots` and `amplification` dictionaries with those lists
before regenerating plots. Rerun the study after changing physical parameters,
the time grid, observables, or converter. The report includes per-observable
means, variances, biases, and predicted RMSE, plus the allocated cost.

All estimates use `tools/estimate_cost.py`, including 5 HQC per program: one
program per Trotter model and nine per LCU model. These are local estimates,
not hardware bills or guaranteed upper bounds. The estimator's ten coinflip
shots do not model physical LCU acceptance; acceptance is calculated from the
dense reference instead. Fixed-count attempts avoid estimating unbounded
retry loops. Measurement-assisted decompositions can still cause small cost
variation between estimates.

## Plots

`magnetization_tfim.png` shows average Z magnetization.
`magnetization_heis.png` has average and staggered X panels from the same shots.
Each panel shows exact evolution, normalized Taylor evolution, ideal conditional
LCU means including amplification, and sampled QIR estimates with one-standard-
error bars. Error bars use accepted samples rather than attempted shots.

Each time point is compiled and validated separately, leaving its `.mlir` and
`.ll` files alongside the script. Every run prints the observable estimates,
accepted-shot counts, and estimated HQC cost per point and total per model.
