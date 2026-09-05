#!/usr/bin/env python3
"""Regenerate MLIR beside every test that declares ``qrisp_program``."""

import argparse
import sys
from pathlib import Path

from qrisp.jasp import Jaspr, make_jaspr


TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent))


from tests.support import load_case


def write_fixture(function, output: Path) -> None:
    jaspr = make_jaspr(function)()
    assert type(jaspr) is Jaspr
    mlir = str(jaspr.to_mlir(lower_stablehlo=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(mlir.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=TESTS)
    parser.add_argument("cases", nargs="*", help="case paths relative to tests/")
    args = parser.parse_args()

    test_cases = ([TESTS / case / "test_case.py" for case in args.cases]
                  if args.cases else TESTS.glob("**/test_case.py"))
    for test_case in sorted(test_cases):
        module = load_case(test_case)
        if not hasattr(module, "qrisp_program"):
            continue
        relative = test_case.parent.relative_to(TESTS) / "input.mlir"
        write_fixture(module.qrisp_program, args.output_dir / relative)


if __name__ == "__main__":
    main()
