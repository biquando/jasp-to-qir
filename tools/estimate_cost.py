#!/usr/bin/env python3
"""Estimate Helios HQC locally from 10 Selene coinflip shots (not an upper bound).

Formula: https://docs.quantinuum.com/systems/trainings/helios/getting_started/costing.html
"""

import argparse
import platform
from pathlib import Path
from tempfile import TemporaryDirectory

from qir_qis import qir_ll_to_bc, qir_to_qis
from selene_sim import BitcodeString, Coinflip, MetricStore, SimpleRuntime, build


def estimate_cost(qir: str, qubits: int, shots: int) -> float:
    target = "aarch64" if platform.machine().lower() in {"arm64", "aarch64"} else "x86-64"
    qis = qir_to_qis(qir_ll_to_bc(qir), target=target)
    metrics = MetricStore()
    with TemporaryDirectory(prefix="qir-cost-") as directory:
        runner = build(BitcodeString(qis), build_dir=Path(directory))
        for shot in runner.run_shots(
            Coinflip(), n_qubits=qubits, n_shots=10,
            runtime=SimpleRuntime(), event_hook=metrics,
        ):
            # Both iterators must be consumed to collect each shot's metrics.
            for _ in shot:
                pass

    counts = []
    for shot in metrics.shots:
        physical = shot["post_runtime"]
        counts.append((
            physical["rxy_individual_count"],  # Rz gates are free.
            physical["rzz_individual_count"],
            physical["measure_individual_count"]
            + physical["measure_leaked_individual_count"]
            + physical["reset_individual_count"]
            + shot["user_program"]["max_allocated"],
        ))
    n1, n2, nm = map(max, zip(*counts))
    return 5 + shots * (n1 + 10 * n2 + 5 * nm) / 5000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", type=Path, help="QIR LLVM IR file (.ll)")
    parser.add_argument("-q", "--qubits", type=int, required=True, help="simulator capacity")
    parser.add_argument("-s", "--shots", type=int, required=True, help="hardware shot count")
    args = parser.parse_args()
    if args.qubits <= 0 or args.shots <= 0:
        parser.error("qubits and shots must be positive")
    cost = estimate_cost(args.program.read_text(), args.qubits, args.shots)
    print(f"Estimated cost: {cost:.6f} HQC")


if __name__ == "__main__":
    main()
