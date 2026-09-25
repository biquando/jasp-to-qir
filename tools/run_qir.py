#!/usr/bin/env python3
"""Compile QIR with qir-qis and simulate with Selene/QuEST."""

import argparse
from multiprocessing import cpu_count
import platform
from pathlib import Path
from typing import TypeAlias

from qir_qis import qir_ll_to_bc, qir_to_qis
from selene_sim import BitcodeString, Quest, build


Bits: TypeAlias = str
Result: TypeAlias = Bits | int
Results: TypeAlias = list[tuple[str, Result]]


def parse_output(value, reverse_bitstrings: bool) -> Bits | int:
    if type(value) is list:
        if reverse_bitstrings:
            value = value[::-1]
        return ''.join(str(v) for v in value)
    else:
        return int(value)


def run(qir: str,
        qubits: int,
        shots: int | None = None,
        reverse_bitstrings: bool = False,
) -> Results | list[Results]:
    target = "aarch64" if platform.machine().lower() in {"arm64", "aarch64"} else "x86-64"
    qis = qir_to_qis(qir_ll_to_bc(qir), target=target)
    runner = build(BitcodeString(qis))

    if shots is not None:
        raw_results = runner.run_shots(Quest(),
                                   n_qubits=qubits,
                                   n_shots=shots,
                                   n_processes=cpu_count())

        all_results: list[Results] = []
        for i, shot in enumerate(raw_results):
            results: Results = []
            for label, value in shot:
                results.append((label, parse_output(value, reverse_bitstrings)))
            all_results.append(results)
        return all_results

    else:
        raw_results = runner.run(Quest(), n_qubits=qubits)
        results = []
        for label, value in raw_results:
            results.append((label, parse_output(value, reverse_bitstrings)))
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", type=Path, help="QIR LLVM IR file")
    parser.add_argument("-q", "--qubits", type=int, required=True, help="QuEST simulator capacity")
    parser.add_argument("-s", "--shots", type=int, help="number of shots")
    parser.add_argument("-r", "--reverse-bitstrings", action="store_true", help="reverse bistrings in output")
    args = parser.parse_args()

    results = run(args.program.read_text(),
                  args.qubits,
                  args.shots,
                  args.reverse_bitstrings)

    def print_shot(shot):
        for result in shot:
            print(f"{result[0]}: {result[1]}")

    if type(results) is Results:
        print_shot(results)
    else:
        for i, shot in enumerate(results):
            print(f"===== SHOT {i+1} =====")
            print_shot(shot)
            print()

if __name__ == "__main__":
    main()
