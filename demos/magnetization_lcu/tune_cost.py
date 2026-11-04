"""Compare LCU choices and allocate shots within the original Trotter HQC budgets.

Run from the repository root with:
    LLVM_BIN=/opt/homebrew/opt/llvm@21/bin ./venv/bin/python -m demos.magnetization_lcu.tune_cost
"""

import json
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from qrisp.jasp import make_jaspr

from demos.magnetization_lcu import magnetization as lcu
# Keep the historical ten-spin budget when the current Trotter benchmark changes.
from demos.magnetization_trotter_backup_2026_10_12 import magnetization as trotter
from tools.estimate_cost import estimate_cost
from tools.jasp_to_qir import convert


def outcome_statistics(model, H, t, oaa_iter):
    """Dense prediction of acceptance, conditional variance, and observable bias."""
    matrix = H.to_array(factor_amount=lcu.n)
    if model == "tfim":
        initial = np.zeros(2**lcu.n)
        initial[0] = 1
    else:
        initial = np.array([1.0])
        for angle in lcu.heis_initial_angles:
            initial = np.kron(initial, [np.cos(angle / 2), np.sin(angle / 2)])
    energies, vectors = np.linalg.eigh(matrix)
    phase = energies * t / lcu.steps
    _, coefficients = lcu.taylor_lcu(H, t)
    encoded = (1 - 1j * phase - 0.5 * phase**2)**lcu.steps / coefficients.sum()
    if oaa_iter == 1:
        # One oblivious amplification round maps B to 3B - 4BB†B.
        encoded = (3 - 4 * np.abs(encoded)**2) * encoded
    weights = vectors.conj().T @ initial
    state = vectors @ (encoded * weights)
    probability = float(np.vdot(state, state).real)
    state /= np.sqrt(probability)
    exact_state = vectors @ (np.exp(-1j * energies * t) * weights)
    statistics = {}
    for name, observable in lcu.observables(model).items():
        mean = float(np.vdot(state, observable @ state).real)
        variance = float(max(0, np.vdot(state, observable @ observable @ state).real - mean**2))
        exact = float(np.vdot(exact_state, observable @ exact_state).real)
        statistics[name] = dict(mean=mean, variance=variance, bias=mean-exact)
    return dict(success_probability=probability, observables=statistics)


def allocate_shots(selected, budget):
    # Minimize sum_i variance_i / (attempts_i * success_probability_i), with
    # sum_i cost_per_attempt_i * attempts_i <= budget - 5 HQC per program.
    # Reserve two attempts per point; t=0 TFIM is deterministic and needs no more.
    cost = np.array([r["cost_per_attempt"] for r in selected])
    # Both Heisenberg observables share each shot and receive equal weight.
    variance = np.array([np.mean([s["variance"] for s in r["observables"].values()])
                         / r["success_probability"] for r in selected])
    remaining = budget - 5 * len(selected) - 2 * cost.sum()
    if remaining <= 0:
        raise ValueError("Budget does not cover the per-program charges and minimum shots.")
    scale = remaining / np.sqrt(variance * cost).sum()
    return (2 + np.floor(scale * np.sqrt(variance / cost))).astype(int)


def predicted_rmse(records, attempts, observable=None):
    # For large accepted counts, E[1 / accepted] is approximately 1 / E[accepted].
    return float(np.sqrt(np.mean([
        s["bias"]**2 + s["variance"] / (count * r["success_probability"])
        for r, count in zip(records, attempts)
        for name, s in r["observables"].items() if observable is None or name == observable
    ])))


def main():
    report = {
        "parameters": dict(n=lcu.n, J=lcu.J, B=lcu.B, times=lcu.times.tolist(), steps=lcu.steps),
        "trotter_parameters": dict(n=trotter.n, J=trotter.J, B=trotter.B,
                                   times=trotter.times.tolist(), steps=trotter.steps,
                                   order=trotter.order, shots=trotter.shots),
        "objective": "Minimize predicted bias squared plus sampling variance, equally weighted "
                     "across time points and plotted observables; enumerate zero/one amplification "
                     "choices and allocate attempted shots within each model's budget.",
        "models": {},
    }
    with TemporaryDirectory(prefix="lcu-cost-") as directory:
        work = Path(directory)
        for model in ("tfim", "heis"):
            # Preserve the original demo's system, grid, Trotter order, and shot count.
            trotter.hamiltonian = model
            source = work / f"trotter_{model}.mlir"
            source.write_text(str(make_jaspr(trotter.main)().to_mlir(lower_stablehlo=True)))
            convert(source, source.with_suffix(".ll"), output_formats="integer")
            budget = estimate_cost(source.with_suffix(".ll").read_text(), trotter.n, trotter.shots)
            print(f"{model}: original Trotter budget = {budget:.4f} HQC", flush=True)
            H = lcu.hamiltonian(model)
            candidates, choices = [], []
            for index, t in enumerate(lcu.times):
                options = []
                for oaa_iter in ([0] if t == 0 else [0, 1]):
                    qir, qubits = lcu.compile_program(
                        model, H, t, work / f"{model}_{index}_{oaa_iter}", oaa_iter)
                    # Fixed-count postselection has no measurement-dependent retry path.
                    # Remove the fixed job charge to recover the cost per attempted shot.
                    cost = (estimate_cost(qir, qubits, 5000) - 5) / 5000
                    record = dict(index=index, time=float(t), oaa=oaa_iter, cost_per_attempt=cost,
                                  **outcome_statistics(model, H, t, oaa_iter))
                    options.append(record)
                candidates.extend(options)
                choices.append(options)
            # Nine time points give only 2**8 combinations. Score each complete
            # allocation so amplification bias and the shared budget both count.
            selected = min(product(*choices), key=lambda records:
                           predicted_rmse(records, allocate_shots(records, budget)))
            counts = allocate_shots(selected, budget)
            selected = [dict(r, shots=int(count)) for r, count in zip(selected, counts)]
            total = sum(5 + r["shots"] * r["cost_per_attempt"] for r in selected)
            plain = [r for r in candidates if r["oaa"] == 0]
            uniform = int((budget - 5 * len(plain)) / sum(r["cost_per_attempt"] for r in plain))
            report["models"][model] = dict(
                budget_hqc=budget, allocated_hqc=total, candidates=candidates, selected=selected,
                predicted_rmse=predicted_rmse(selected, counts),
                predicted_rmse_by_observable={name: predicted_rmse(selected, counts, name)
                                              for name in lcu.observable_weights(model)},
                uniform_unamplified_shots=uniform,
                uniform_unamplified_rmse=predicted_rmse(plain, [uniform] * len(plain)))
            print(f"{model}: shots = {counts.tolist()}", flush=True)
            print(f"{model}: amplification = {[r['oaa'] for r in selected]}", flush=True)
            print(f"{model}: allocated cost = {total:.4f} HQC", flush=True)
    path = Path(__file__).with_name("cost_study.json")
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved {path}; use its selected settings in magnetization.py.")


if __name__ == "__main__":
    main()
