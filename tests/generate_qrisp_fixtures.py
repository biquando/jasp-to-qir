#!/usr/bin/env python3
"""Regenerate MLIR beside every test that declares ``qrisp_program``."""

import argparse
import contextlib
import importlib.util
import io
import sys
from pathlib import Path

from qrisp.jasp import Jaspr, make_jaspr


TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent))


def load_case(path: Path):
    name = "fixture_" + "_".join(path.parent.parts[-2:])
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load test case {path}")
    module = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(module)
    return module


def write_fixture(function, output: Path) -> None:
    jaspr = make_jaspr(function)()
    assert type(jaspr) is Jaspr
    mlir = str(jaspr.to_mlir(lower_stablehlo=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(mlir.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=TESTS)
    args = parser.parse_args()

    test_cases = (
        path
        for category in ("validation", "statevector", "semantics")
        for path in (TESTS / category).glob("*/test_case.py")
    )
    for test_case in sorted(test_cases):
        module = load_case(test_case)
        if not hasattr(module, "qrisp_program"):
            continue
        relative = test_case.parent.relative_to(TESTS) / "input.mlir"
        write_fixture(module.qrisp_program, args.output_dir / relative)


if __name__ == "__main__":
    main()
