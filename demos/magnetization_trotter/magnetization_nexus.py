import numpy as np
import matplotlib.pyplot as plt

filename = "magnetization_nexus.txt"

n_qubits = 10
n_steps = 30
dt = 0.1
J = 1.0
B = 3.0

# Accumulate magnetization and number of shots for each time step.
mag_sum = np.zeros(n_steps, dtype=float)
counts = np.zeros(n_steps, dtype=int)

with open(filename, "r") as f:
    for line in f:
        if not line.startswith("OUTPUT"):
            continue

        parts = line.strip().split("\t")

        value = int(parts[2])
        result_name = parts[3]

        # "result_17" -> 17
        t_idx = int(result_name.split("_")[1])

        # Equivalent to converting to a 10-bit string and counting 1s.
        n_ones = value.bit_count()

        # <Z> averaged across the 10 qubits for this shot/time step.
        magnetization = 1.0 - 2.0 * n_ones / n_qubits

        mag_sum[t_idx] += magnetization
        counts[t_idx] += 1

def exact_tfim_magnetization(times):
    # Build H = -J sum Z_i Z_{i+1} - B sum X_i in the computational basis.
    basis = np.arange(2**n_qubits)
    spins = 1 - 2 * ((basis[:, None] >> np.arange(n_qubits)) & 1)
    hamiltonian = np.diag(-J * np.sum(spins[:, :-1] * spins[:, 1:], axis=1))
    for i in range(n_qubits):
        hamiltonian[basis, basis ^ (1 << i)] -= B

    energies, eigenvectors = np.linalg.eigh(hamiltonian)
    # |psi(t)> = exp(-i H t)|0>, with hbar = 1 and no Trotter approximation.
    coefficients = eigenvectors[0].conj()
    states = (np.exp(-1j * np.outer(times, energies)) * coefficients) @ eigenvectors.T
    return np.abs(states)**2 @ spins.mean(axis=1)


# Average over all shots.
magnetization_avg = mag_sum / counts

times = np.arange(n_steps) * dt
times_exact = np.linspace(0.0, 3.0, 500)

plt.plot(times_exact, exact_tfim_magnetization(times_exact), label="Exact evolution")
plt.plot(times, magnetization_avg, ".", label="Trotter on Helios (5000 shots)")
plt.xlabel("Time")
plt.ylabel(r"$\langle Z \rangle$")
plt.tight_layout()
plt.legend()
plt.show()
