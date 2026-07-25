#!/usr/bin/env python3
"""Compile textual QIR with qir-qis and run one shot with Selene/QuEST."""

import argparse
import platform
from pathlib import Path

from qir_qis import qir_ll_to_bc, qir_to_qis
from selene_sim import BitcodeString, Quest, build


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("program", type=Path, help="QIR LLVM IR file")
parser.add_argument("n_qubits", type=int, help="QuEST simulator capacity")
args = parser.parse_args()

target = "aarch64" if platform.machine().lower() in {"arm64", "aarch64"} else "x86-64"
qir = args.program.read_text(encoding="utf-8")
qis = qir_to_qis(qir_ll_to_bc(qir), target=target)
runner = build(BitcodeString(qis))

for label, value in runner.run(Quest(), n_qubits=args.n_qubits):
    print(f"{label}: {value}")
