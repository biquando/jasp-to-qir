#!/usr/bin/env python3
"""Compile textual QIR with qir-qis and run one shot with Selene/QuEST."""

import argparse
import platform
from pathlib import Path

from qir_qis import qir_ll_to_bc, qir_to_qis
from selene_sim import BitcodeString, Quest, build


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("program", type=Path, help="QIR LLVM IR file")
parser.add_argument("-q", "--qubits", type=int, required=True, help="QuEST simulator capacity")
parser.add_argument("-s", "--shots", type=int, help="number of shots")
args = parser.parse_args()

target = "aarch64" if platform.machine().lower() in {"arm64", "aarch64"} else "x86-64"
qir = args.program.read_text(encoding="utf-8")
qis = qir_to_qis(qir_ll_to_bc(qir), target=target)
runner = build(BitcodeString(qis))

if args.shots is not None:
    results = runner.run_shots(Quest(), n_qubits=args.qubits, n_shots=args.shots)
    for i, shot in enumerate(results):
        print(f'===== SHOT {i+1} =====')
        for label, value in shot:
            if type(value) is list:
                print(f"{label}: {''.join([str(v) for v in value])}")
            else:
                print(f"{label}: {value}")
        print()
else:
    results = runner.run(Quest(), n_qubits=args.qubits)
    for label, value in results:
        if type(value) is list:
            print(f"{label}: {''.join([str(v) for v in value])}")
        else:
            print(f"{label}: {value}")
