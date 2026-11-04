"""Run the two-spin benchmark shared with the LCU demo, using Trotter evolution."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from qir_qis import qir_ll_to_bc, validate_qir
from qrisp import QuantumVariable, h, measure, reset, ry
from qrisp.operators import QubitOperator, X, Y, Z
from qrisp.jasp import make_jaspr

from tools.jasp_to_qir import convert
from tools.run_qir import run
from tools.estimate_cost import estimate_cost

hamiltonian = "tfim"
n = 10
J = 1.0
B = 1.0
steps = 10
order = 1
times = np.linspace(0.0, 3.2, 9)
shots = 250
heis_initial_angles = np.where(np.arange(n) % 2 == 0, np.pi / 4, -np.pi / 8)

def tfim(t, register):
    H = QubitOperator()
    for i in range(n-1):
        H += -J * Z(i) * Z(i+1)
    for i in range(n):
        H += -B * X(i)

    U = H.trotterization(order=order)
    U(register, t=t, steps=steps)

    result = measure(register)
    reset(register)
    return result

def heis(t, register):
    for i, angle in enumerate(heis_initial_angles):
        ry(angle, register[i])

    H = QubitOperator()
    for i in range(n-1):
        H += -J * X(i) * X(i+1)
        H += -J * Y(i) * Y(i+1)
        H += -J * Z(i) * Z(i+1)
    for i in range(n):
        H += -B * Z(i)

    U = H.trotterization(order=order)
    U(register, t=t, steps=steps)

    h(register)  # Rotate X-basis measurements into the computational basis.
    result = measure(register)
    reset(register)
    return result


def main():
    # Reuse qubits, resetting to |0> between independent time points.
    register = QuantumVariable(n)
    if hamiltonian == "tfim":
        results = tuple(tfim(t, register) for t in times)
    elif hamiltonian == "heis":
        results = tuple(heis(t, register) for t in times)
    else:
        return
    register.delete()
    return results


def exact_tfim_magnetization(times):
    # Build H = -J sum Z_i Z_{i+1} - B sum X_i in the computational basis.
    basis = np.arange(2**n)
    spins = 1 - 2 * ((basis[:, None] >> np.arange(n)) & 1)
    hamiltonian = np.diag(-J * np.sum(spins[:, :-1] * spins[:, 1:], axis=1))
    for i in range(n):
        hamiltonian[basis, basis ^ (1 << i)] -= B

    energies, eigenvectors = np.linalg.eigh(hamiltonian)
    # |psi(t)> = exp(-i H t)|0>, with hbar = 1 and no Trotter approximation.
    coefficients = eigenvectors[0].conj()
    states = (np.exp(-1j * np.outer(times, energies)) * coefficients) @ eigenvectors.T
    return np.abs(states)**2 @ spins.mean(axis=1)


def exact_heis_magnetization(times, staggered=False):
    """Exact average or staggered X magnetization from the Ry product state."""
    # H = -J sum (X_i X_{i+1} + Y_i Y_{i+1} + Z_i Z_{i+1}) - B sum Z_i.
    basis = np.arange(2**n)
    spins = 1 - 2 * ((basis[:, None] >> np.arange(n)) & 1)
    bonds = spins[:, :-1] * spins[:, 1:]
    hamiltonian = np.diag(-J * bonds.sum(axis=1) - B * spins.sum(axis=1))
    for i in range(n - 1):
        flipped = basis ^ (1 << i) ^ (1 << (i + 1))
        # XX and YY cancel for aligned spins and add for opposite spins.
        hamiltonian[basis, flipped] -= J * (1 - bonds[:, i])

    energies, eigenvectors = np.linalg.eigh(hamiltonian)
    initial_state = np.prod(np.where(
        spins == 1, np.cos(heis_initial_angles / 2), np.sin(heis_initial_angles / 2)
    ), axis=1)
    coefficients = eigenvectors.conj().T @ initial_state
    states = (np.exp(-1j * np.outer(times, energies)) * coefficients) @ eigenvectors.T
    # X_i flips bit i in the computational basis.
    return sum(
        (-1 if staggered and i % 2 else 1)
        * np.sum(states.conj() * states[:, basis ^ (1 << i)], axis=1).real
        for i in range(n)
    ) / n


if __name__ == "__main__":
    output_dir = Path(__file__).parent
    report = dict(n=n, J=J, B=B, times=times.tolist(), steps=steps, order=order,
                  shots_per_time=shots, models={})
    for model, title, axis in [("tfim", "TFIM", "Z"), ("heis", "Heisenberg", "X")]:
        hamiltonian = model
        mlir_path = output_dir / f"{model}.mlir"
        qir_path = mlir_path.with_suffix(".ll")
        print(f"{title}: compiling {shots} shots per time point", flush=True)
        mlir_path.write_text(str(make_jaspr(main)().to_mlir(lower_stablehlo=True)))
        convert(mlir_path, qir_path, output_formats="integer")
        qir = qir_path.read_text()
        validate_qir(qir_ll_to_bc(qir))
        results = run(qir, qubits=n, shots=shots)
        assert len(results) == shots
        assert all(len(shot) == len(times) for shot in results)
        cost = estimate_cost(qir, n, shots)

        # One shot returns a packed result per time; q0 is the least-significant bit.
        packed = np.array([[int(value) for _, value in shot] for shot in results])
        spins = 1 - 2 * ((packed[:, :, None] >> np.arange(n)) & 1)
        weights = {"average": np.ones(n) / n}
        if model == "heis":
            weights["staggered"] = (-1.0)**np.arange(n) / n

        figure, axes = plt.subplots(len(weights), 1, squeeze=False, sharex=True,
                                    figsize=(7, 4 * len(weights)))
        exact_times = np.linspace(times[0], times[-1], 500)
        observations = {}
        for plot, (name, coefficients) in zip(axes[:, 0], weights.items()):
            samples = spins @ coefficients
            means = samples.mean(axis=0)
            errors = samples.std(axis=0, ddof=1) / np.sqrt(shots)
            if model == "tfim":
                exact = exact_tfim_magnetization(exact_times)
                exact_points = exact_tfim_magnetization(times)
            else:
                exact = exact_heis_magnetization(exact_times, name == "staggered")
                exact_points = exact_heis_magnetization(times, name == "staggered")
            rmse = float(np.sqrt(np.mean((means - exact_points)**2)))
            observations[name] = dict(mean=means.tolist(), standard_error=errors.tolist(),
                                      exact=exact_points.tolist(), rmse=rmse)
            plot.plot(exact_times, exact, label="Exact evolution")
            plot.errorbar(times, means, yerr=errors, fmt=".", capsize=2,
                          label=f"QIR (Trotter, {shots} shots)")
            plot.set_ylabel(f"{name.capitalize()} magnetization ({axis})")
            print(f"{title}: {name} RMSE = {rmse:.5f}", flush=True)
        axes[-1, 0].set_xlabel("Time")
        figure.suptitle(f"{title}: {n} spins, J={J:g}, B={B:g}", y=0.99)
        height = figure.get_figheight()
        handles, labels = axes[0, 0].get_legend_handles_labels()
        figure.legend(handles, labels, loc="upper center", ncol=2, fontsize="small",
                      bbox_to_anchor=(0.5, 1 - 0.35 / height))
        figure.tight_layout(rect=(0, 0, 1, 1 - 0.65 / height))
        plot_path = output_dir / f"magnetization_{model}.png"
        figure.savefig(plot_path, dpi=150)
        report["models"][model] = dict(estimated_hqc=cost, observables=observations)
        print(f"Saved {plot_path}; estimated cost {cost:.2f} HQC", flush=True)
    (output_dir / "benchmark_results.json").write_text(json.dumps(report, indent=2) + "\n")
    plt.show()
