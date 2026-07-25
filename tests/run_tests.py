#!/usr/bin/env python3
"""Run the complete Jasp-to-QIR regression suite.

Invoke this file with the repository virtual environment::

    ./venv/bin/python tests/run_tests.py

The suite has five phases:

1. Regenerate Qrisp fixtures and compare them byte-for-byte with the checked-in
   files under ``tests/fixtures/qrisp``.
2. Convert every Qrisp fixture in both static and dynamic resource modes, then
   run the QIR and LLVM validators.
3. Inspect representative LLVM output for semantic properties that structural
   validation alone cannot establish.
4. Check diagnostics for invalid or unsupported Jasp input.
5. Verify the driver's ``--keep-intermediates`` contract.

All generated files and caches live in a per-run directory beneath the ignored
``tests/.tmp`` directory. The per-run directory is removed automatically. Set
``LLVM_BIN`` to override the default Homebrew LLVM tool directory.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

# Generated inputs and deliberately invalid programs have separate ownership.
FIXTURES = TESTS / "fixtures"
QRISP = FIXTURES / "qrisp"
INVALID = FIXTURES / "invalid"
TEMP_ROOT = TESTS / ".tmp"
DRIVER = ROOT / "tools/jasp_to_ll.py"
VALIDATOR = ROOT / "tools/validate_qir.py"
GENERATOR = TESTS / "generate_qrisp_fixtures.py"
LLVM_BIN = Path(os.environ.get("LLVM_BIN", "/opt/homebrew/opt/llvm/bin"))
OPT = LLVM_BIN / "opt"


class TestFailure(RuntimeError):
    """A regression check failed."""


def run(
    command: list[str | Path],
    *,
    env: dict[str, str] | None = None,
    expect_failure: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a repository command and enforce its expected exit behavior.

    Output is captured to keep successful runs concise. If the command exits
    contrary to ``expect_failure``, both stdout and stderr are included in the
    raised ``TestFailure``.
    """

    rendered = [str(part) for part in command]
    result = subprocess.run(
        rendered,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    failed = result.returncode != 0
    if failed != expect_failure:
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        expectation = "failure" if expect_failure else "success"
        raise TestFailure(
            f"expected {expectation}: {' '.join(rendered)}\n{output}".rstrip()
        )
    return result


def require(condition: bool, message: str) -> None:
    """Raise a test failure with ``message`` when ``condition`` is false."""

    if not condition:
        raise TestFailure(message)


def require_contains(path: Path, *patterns: str) -> str:
    """Require every literal pattern in a UTF-8 file and return its text."""

    text = path.read_text(encoding="utf-8")
    for pattern in patterns:
        require(pattern in text, f"{path.name}: missing {pattern!r}")
    return text


def require_adjacent(text: str, measurement: str, recording: str, count: int) -> None:
    """Require ``count`` measurements to be followed by an output record.

    Immediate adjacency matters because recording a result later could change
    conditional-program output by recording a measurement from an untaken path.
    """

    lines = text.splitlines()
    adjacent = sum(
        measurement in line
        and index + 1 < len(lines)
        and recording in lines[index + 1]
        for index, line in enumerate(lines)
    )
    require(adjacent == count, f"expected {count} adjacent output records, got {adjacent}")


def verify_qrisp_fixtures(temp: Path) -> None:
    """Regenerate Qrisp fixtures in isolation and reject checked-in drift."""

    generated = temp / "generated-qrisp"
    cache = temp / "cache"
    environment = os.environ.copy()
    environment["MPLCONFIGDIR"] = str(cache / "matplotlib")
    environment["XDG_CACHE_HOME"] = str(cache)
    run([sys.executable, GENERATOR, "--output-dir", generated], env=environment)

    checked_in = {path.name: path for path in QRISP.glob("*.mlir")}
    fresh = {path.name: path for path in generated.glob("*.mlir")}
    require(
        checked_in.keys() == fresh.keys(),
        "Qrisp fixture names differ; regenerate with "
        f"{sys.executable} {GENERATOR.relative_to(ROOT)}",
    )
    changed = [
        name
        for name in checked_in
        if checked_in[name].read_bytes() != fresh[name].read_bytes()
    ]
    require(
        not changed,
        "stale Qrisp fixtures: "
        + ", ".join(changed)
        + f"; regenerate with {sys.executable} {GENERATOR.relative_to(ROOT)}",
    )
    print(f"PASS Qrisp fixture freshness ({len(fresh)} fixtures)")


def convert_and_validate(fixture: Path, mode: str, temp: Path) -> Path:
    """Convert one fixture, validate its QIR, and return the output path.

    Static mode intentionally omits ``--resource-management`` so the suite also
    protects the driver's documented default. Dynamic mode passes it explicitly.
    """

    category = fixture.parent.name
    output = temp / f"{category}-{fixture.stem}.{mode}.ll"
    command: list[str | Path] = [sys.executable, DRIVER]
    if mode == "dynamic":
        command.extend(["--resource-management", mode])
    command.extend([fixture, output])
    run(command)
    run([sys.executable, VALIDATOR, output])
    run([OPT, "-passes=verify", "-disable-output", output])
    stem = output.with_suffix("")
    for suffix in ("llvm.mlir", "raw.ll"):
        require(not stem.with_suffix(f".{suffix}").exists(), f"unexpected {suffix}")
    return output


def verify_valid_fixtures(temp: Path) -> dict[tuple[str, str], Path]:
    """Convert and validate every valid fixture in both resource modes."""

    fixtures = sorted(QRISP.glob("*.mlir"))
    outputs: dict[tuple[str, str], Path] = {}
    for mode in ("static", "dynamic"):
        for fixture in fixtures:
            outputs[(mode, fixture.name)] = convert_and_validate(fixture, mode, temp)
        print(f"PASS {mode} conversion and validation ({len(fixtures)} fixtures)")
    return outputs


def verify_semantics(outputs: dict[tuple[str, str], Path], temp: Path) -> None:
    """Check QIR properties not fully covered by structural validators."""

    default_basic = outputs[("static", "basic.mlir")]
    explicit_static = temp / "basic.explicit-static.ll"
    run(
        [
            sys.executable,
            DRIVER,
            "--resource-management",
            "static",
            QRISP / "basic.mlir",
            explicit_static,
        ]
    )
    require(
        default_basic.read_bytes() == explicit_static.read_bytes(),
        "default resource mode differs from explicit static mode",
    )

    require_contains(outputs[("static", "adaptive.mlir")], "br i1")
    require_contains(
        outputs[("static", "loop.mlir")], '!"backwards_branching", i2 1'
    )
    require_contains(
        outputs[("static", "many_results.mlir")],
        '@label10 = internal constant [7 x i8] c"bit_10\\00"',
    )
    reset = require_contains(
        outputs[("static", "reset_array.mlir")],
        "declare void @__quantum__qis__reset__body(ptr) #1",
    )
    require(
        "__quantum__qis__reset__body({" not in reset,
        "reset received an array descriptor",
    )
    conditional = require_contains(outputs[("static", "conditional_measurement.mlir")])
    require_adjacent(
        conditional,
        "call void @__quantum__qis__mz__body",
        "call void @__quantum__rt__result_record_output",
        2,
    )

    dynamic = require_contains(
        outputs[("dynamic", "basic.mlir")],
        '!"dynamic_qubit_management", i1 true',
        '!"dynamic_result_management", i1 true',
        '!"arrays", i1 true',
        "__quantum__rt__qubit_array_allocate(i64 2",
        "__quantum__rt__result_array_allocate(i64 2",
        "__quantum__rt__result_array_record_output(i64 2",
        "__quantum__rt__result_array_release(i64 2",
    )
    require(
        "required_num_" not in dynamic and "inttoptr" not in dynamic,
        "dynamic output contains static resource metadata or handles",
    )
    require_contains(
        outputs[("dynamic", "lifecycle.mlir")],
        "__quantum__rt__qubit_array_allocate(i64 1",
        "__quantum__rt__qubit_array_release(i64 1",
    )
    dynamic_conditional = require_contains(
        outputs[("dynamic", "conditional_measurement.mlir")]
    )
    require(
        dynamic_conditional.count(
            "call ptr @__quantum__rt__result_allocate(ptr null)"
        )
        == 2,
        "conditional measurement did not allocate two scalar results",
    )
    require(
        dynamic_conditional.count(
            "  call void @__quantum__rt__result_release"
        )
        == 2,
        "conditional measurement did not release two scalar results",
    )
    require_adjacent(
        dynamic_conditional,
        "call void @__quantum__qis__mz__body",
        "call void @__quantum__rt__result_record_output",
        2,
    )
    print("PASS focused QIR semantics")


def expect_conversion_failure(
    fixture: Path,
    expected: str,
    temp: Path,
    *,
    mode: str = "static",
) -> None:
    """Require conversion to fail cleanly with a specific diagnostic."""

    output = temp / f"invalid-{fixture.stem}-{mode}.ll"
    command: list[str | Path] = [sys.executable, DRIVER]
    if mode == "dynamic":
        command.extend(["--resource-management", mode])
    command.extend([fixture, output])
    result = run(command, expect_failure=True)
    require(expected in result.stderr, f"{fixture.name}: missing error {expected!r}")
    require("Traceback" not in result.stderr, f"{fixture.name}: printed a traceback")


def verify_invalid_fixtures(temp: Path) -> None:
    """Check unsupported operations, invalid types, and allocation errors."""

    for operation in ("slice", "fuse", "parity"):
        expect_conversion_failure(
            INVALID / f"unsupported_{operation}.mlir",
            f"Unsupported Jasp operation 'jasp.{operation}'",
            temp,
        )

    allocation_error = "QIR array backing storage requires a compile-time constant size"
    for mode in ("static", "dynamic"):
        expect_conversion_failure(
            INVALID / "dynamic_allocation.mlir", allocation_error, temp, mode=mode
        )
    expect_conversion_failure(
        INVALID / "invalid_measure.mlir",
        "requires result type 'tensor<i1>' for operand type '!jasp.Qubit'",
        temp,
    )

    gate_template = (INVALID / "unsupported_gate.mlir").read_text(encoding="utf-8")
    for gate in ("p", "gphase", "unknown_gate"):
        fixture = temp / f"unsupported-gate-{gate}.mlir"
        fixture.write_text(gate_template.replace('"p"', f'"{gate}"'), encoding="utf-8")
        expect_conversion_failure(fixture, f"Unsupported Jasp gate '{gate}'", temp)
    print("PASS expected conversion failures (9 cases)")


def verify_intermediates(temp: Path) -> None:
    """Verify the documented intermediate files are retained."""

    output = temp / "kept.ll"
    run(
        [
            sys.executable,
            DRIVER,
            "--keep-intermediates",
            QRISP / "basic.mlir",
            output,
        ]
    )
    stem = output.with_suffix("")
    for suffix in ("llvm.mlir", "raw.ll"):
        require(stem.with_suffix(f".{suffix}").is_file(), f"missing kept {suffix}")
    print("PASS --keep-intermediates")


def main() -> int:
    """Run all phases in one automatically cleaned repository-local directory."""

    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="run-", dir=TEMP_ROOT) as directory:
            temp = Path(directory)
            verify_qrisp_fixtures(temp)
            outputs = verify_valid_fixtures(temp)
            verify_semantics(outputs, temp)
            verify_invalid_fixtures(temp)
            verify_intermediates(temp)
    except (OSError, TestFailure) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    finally:
        if TEMP_ROOT.exists() and not any(TEMP_ROOT.iterdir()):
            TEMP_ROOT.rmdir()
    print("PASS complete test suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
