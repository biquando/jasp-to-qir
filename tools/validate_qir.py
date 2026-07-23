#!/usr/bin/env python3
"""Validate textual QIR with qir-qis."""

import argparse
from pathlib import Path

from qir_qis import qir_ll_to_bc, validate_qir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()

    llvm_ir = args.input.read_text(encoding="utf-8")
    validate_qir(qir_ll_to_bc(llvm_ir))


if __name__ == "__main__":
    main()
