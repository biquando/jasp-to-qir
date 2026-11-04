"""Second-order Taylor evolution with Qrisp LCU, QIR, and Selene/QuEST.

Run from the repository root with:
    LLVM_BIN=/opt/homebrew/opt/llvm@21/bin ./venv/bin/python -m demos.magnetization_lcu.magnetization
"""

from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
from qir_qis import qir_ll_to_bc, validate_qir
from qrisp import QuantumVariable, gphase, h, inner_LCU, measure, prepare, reset, ry
from qrisp.jasp import make_jaspr
from qrisp.operators import QubitOperator, X, Y, Z

from tools.jasp_to_qir import convert
from tools.run_qir import run
from tools.estimate_cost import estimate_cost

n = 3
J = 1.0
B = 1.0
times = np.linspace(0.0, 3.2, 9)
steps = 30
# Selected by tune_cost.py for the parameters above. Shots count LCU attempts;
# only successful attempts contribute to the magnetization estimate.
# shots = {
#     "tfim": [2, 555, 874, 1070, 1078, 821, 584, 896, 639],
#     "heis": [23366, 2411, 2508, 2450, 4335, 2366, 2493, 2481, 5032],
# }
# amplification = {
#     "tfim": [0, 1, 1, 1, 1, 1, 1, 0, 1],
#     "heis": [0, 1, 1, 1, 0, 1, 1, 1, 0],
# }
shots = {
    "tfim": [250] * len(times),
    "heis": [500] * len(times),
}
amplification = {
    "tfim": [0, 1, 1, 1, 1, 1, 1, 1, 1],
    "heis": [0, 1, 1, 1, 0, 1, 1, 1, 1],
}
# budgets = {"tfim": 3697.5, "heis": 10987.5}  # Original ten-spin Trotter runs, HQC.
heis_initial_angles = np.where(np.arange(n) % 2 == 0, np.pi / 4, -np.pi / 8)


def hamiltonian(model):
    H = QubitOperator()
    for i in range(n - 1):
        H += -J * Z(i) * Z(i + 1)
        if model == "heis":
            H += -J * (X(i) * X(i + 1) + Y(i) * Y(i + 1))
    for i in range(n):
        H += -B * (X(i) if model == "tfim" else Z(i))
    return H


def observable_weights(model):
    weights = {"average": np.ones(n) / n}
    if model == "heis":
        weights["staggered"] = (-1.0)**np.arange(n) / n
    return weights


def observables(model):
    pauli = Z if model == "tfim" else X
    matrices = {}
    for name, weights in observable_weights(model).items():
        operator = sum(weight * pauli(i) for i, weight in enumerate(weights))
        matrices[name] = operator.to_array(factor_amount=n)
    return matrices


def taylor_lcu(H, t):
    # Combine short second-order Taylor steps classically, then apply one LCU.
    # QubitOperator multiplication combines Pauli products and like terms.
    dt = t / steps
    A = (1 - 1j * dt * H - 0.5 * dt**2 * (H * H)) ** steps
    unitaries, coefficients = [], []
    # A.unitaries() would hermitize A and lose the -i*t*H contribution.
    for term, coefficient in A.terms_dict.items():
        if abs(coefficient) == 0:
            continue

        def unitary(register, pauli=term.unitary(), phase=np.angle(coefficient)):
            pauli(register)
            # This phase becomes relative when SELECT controls the unitary.
            gphase(float(phase), register[0])

        unitaries.append(unitary)
        coefficients.append(abs(coefficient))
    return unitaries, np.array(coefficients)


def compile_program(model, H, t, output_path, oaa_iter=0):
    unitaries, coefficients = taylor_lcu(H, t)
    ancillas = (len(unitaries) - 1).bit_length()

    def prepare_operand():
        register = QuantumVariable(n)
        if model == "heis":
            for i, angle in enumerate(heis_initial_angles):
                ry(angle, register[i])
        return register

    def prepare_coefficients(case):
        prepare(case, np.sqrt(coefficients))

    def main():
        # t=0 is identity; bypass LCU's zero-qubit selector in this case.
        if t == 0:
            register = prepare_operand()
            success = True
        else:
            case, register = inner_LCU(prepare_operand, prepare_coefficients, unitaries,
                                      oaa_iter=oaa_iter)
            success = measure(case) == 0
            reset(case)
            case.delete()
        if model == "heis":
            h(register)  # Measure X magnetization.
        return success, measure(register)

    mlir_path = output_path.with_suffix(".mlir")
    qir_path = output_path.with_suffix(".ll")
    mlir_path.write_text(str(make_jaspr(main)().to_mlir(lower_stablehlo=True)))
    convert(mlir_path, qir_path, output_formats="integer")
    qir = qir_path.read_text()
    validate_qir(qir_ll_to_bc(qir))
    # Allow space for the selector and SELECT's temporary control qubits.
    return qir, n + 2 * ancillas + 1


def simulate(model, H, t, output_path, attempts, oaa_iter=0):
    qir, qubits = compile_program(model, H, t, output_path, oaa_iter)
    cost = estimate_cost(qir, qubits, attempts)
    results = run(qir, qubits=qubits, shots=attempts)
    # Failed LCU attempts are paid for but do not enter the observable average.
    accepted = [int(shot[-1][1]) for shot in results if int(shot[0][1]) == 1]
    if len(accepted) < 2:
        raise RuntimeError("Too few successful LCU attempts; increase the shot count.")
    # Packed QIR measurements put q0 in the least-significant bit.
    spins = 1 - 2 * ((np.array(accepted)[:, None] >> np.arange(n)) & 1)
    statistics = {}
    for name, weights in observable_weights(model).items():
        samples = spins @ weights
        statistics[name] = (samples.mean(), samples.std(ddof=1) / np.sqrt(len(samples)))
    return statistics, len(accepted), cost


def reference_magnetization(model, H, ts, oaa_iter=0):
    """Exact and conditional Taylor/LCU expectations, evaluated classically."""
    ts = np.asarray(ts)
    matrix = H.to_array(factor_amount=n)
    if model == "tfim":
        initial = np.zeros(2**n)
        initial[0] = 1
    else:
        initial = np.array([1.0])
        # QubitOperator.to_array() orders tensor factors q0, q1, ... .
        for angle in heis_initial_angles:
            initial = np.kron(initial, [np.cos(angle / 2), np.sin(angle / 2)])
    energies, eigenvectors = np.linalg.eigh(matrix)
    coefficients = eigenvectors.conj().T @ initial
    states = (np.exp(-1j * np.outer(ts, energies)) * coefficients) @ eigenvectors.T
    phase = np.outer(ts / steps, energies)
    encoded = (1 - 1j * phase - 0.5 * phase**2)**steps
    if oaa_iter == 1:
        normalization = np.array([taylor_lcu(H, t)[1].sum() for t in ts])
        encoded /= normalization[:, None]
        encoded *= 3 - 4 * np.abs(encoded)**2
    taylor_states = (encoded * coefficients) @ eigenvectors.T
    taylor_states /= np.linalg.norm(taylor_states, axis=1)[:, None]

    def expectation(vectors, observable):
        return np.einsum("bi,ij,bj->b", vectors.conj(), observable, vectors).real

    return {name: (expectation(states, observable), expectation(taylor_states, observable))
            for name, observable in observables(model).items()}


if __name__ == "__main__":
    output_dir = Path(__file__).parent
    for model, title, axis in [("tfim", "TFIM", "Z"), ("heis", "Heisenberg", "X")]:
        start = perf_counter()
        H = hamiltonian(model)
        magnetization = {name: [] for name in observable_weights(model)}
        errors = {name: [] for name in magnetization}
        ideal = {name: [] for name in magnetization}
        total_cost = 0
        for index, t in enumerate(times):
            statistics, accepted, cost = simulate(
                model, H, t, output_dir / f"{model}_{index:02d}",
                shots[model][index], amplification[model][index])
            reference = reference_magnetization(model, H, [t], amplification[model][index])
            for name, (value, error) in statistics.items():
                magnetization[name].append(value)
                errors[name].append(error)
                ideal[name].append(reference[name][1][0])
            total_cost += cost
            estimates = ", ".join(f"{name}={value:.4f} +/- {error:.4f}"
                                  for name, (value, error) in statistics.items())
            print(f"{title}: t={t:.2f}, {estimates}, "
                  f"accepted={accepted}/{shots[model][index]}, cost={cost:.2f} HQC", flush=True)

        exact_times = np.linspace(times[0], times[-1], 500)
        reference = reference_magnetization(model, H, exact_times)
        figure, axes = plt.subplots(len(magnetization), 1, squeeze=False, sharex=True,
                                    figsize=(7, 4 * len(magnetization)))
        for plot, name in zip(axes[:, 0], magnetization):
            exact, taylor = reference[name]
            plot.plot(exact_times, exact, label="Exact evolution")
            plot.plot(exact_times, taylor, "--", label=f"Exact LCU")
            # plot.plot(times, ideal[name], "o", fillstyle="none", label="Ideal LCU (incl. amplification)")
            if all(x == shots[model][0] for x in shots[model]):
                plot.errorbar(times, magnetization[name], yerr=errors[name], fmt=".", capsize=2,
                              label=f"QIR (LCU, {shots[model][0]} shots)")
            else:
                plot.errorbar(times, magnetization[name], yerr=errors[name], fmt=".", capsize=2,
                              label="QIR (LCU, varying shots)")
            plot.set_ylabel(f"{name.capitalize()} magnetization ({axis})")
        axes[-1, 0].set_xlabel("Time")
        figure.suptitle(f"{title}: {n} spins, J={J:g}, B={B:g}", y=0.99)
        height = figure.get_figheight()
        handles, labels = axes[0, 0].get_legend_handles_labels()
        figure.legend(handles, labels, loc="upper center", ncol=2, fontsize="small",
                      bbox_to_anchor=(0.5, 1 - 0.35 / height))
        figure.tight_layout(rect=(0, 0, 1, 1 - 0.8 / height))
        plot_path = output_dir / f"magnetization_{model}.png"
        figure.savefig(plot_path, dpi=150)
        print(f"Saved {plot_path} ({perf_counter() - start:.1f}s); "
              # f"estimated cost {total_cost:.2f} / {budgets[model]:.2f} HQC", flush=True)
              f"estimated cost {total_cost:.2f} HQC", flush=True)
    plt.show()
