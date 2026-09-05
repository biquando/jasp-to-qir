#!/usr/bin/env python3
"""Shared mechanics for the categorized Jasp-to-QIR tests.

Invoke this file with the repository virtual environment::

    ./venv/bin/python tests/run_tests.py

Test modules contain one test case each and delegate process execution,
conversion, and semantic comparison to this module. ``run_tests.py``
is intentionally limited to unittest discovery and suite lifecycle.
"""

from __future__ import annotations

import os
import contextlib
import importlib.util
import io
import json
import math
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

TEMP_ROOT = TESTS / ".tmp"
RESULTS = TESTS / "results"
SEMANTIC_REPORT = RESULTS / "semantic_results.txt"
DRIVER = ROOT / "tools/jasp_to_qir.py"
VALIDATOR = ROOT / "tools/validate_qir.py"
GENERATOR = TESTS / "generate_qrisp_fixtures.py"
QRISP_STATEVECTOR = ROOT / "tools/qrisp_statevector.py"
QIR_STATEVECTOR = ROOT / "tools/qir_statevector.py"
LLVM_BIN = os.environ.get("LLVM_BIN")
OPT = Path(LLVM_BIN) / "opt" if LLVM_BIN else "opt"
STATEVECTOR_TOLERANCE = 1e-6
RESOURCE_MODES = ("static", "dynamic")

_temp_owner: tempfile.TemporaryDirectory[str] | None = None
_temp: Path | None = None
REPORT: list[str] = []
_saved_environment: dict[str, str | None] = {}


def start_session() -> Path:
    """Create the suite's shared temporary directory and simulator caches."""

    global _temp_owner, _temp
    if _temp is not None:
        raise RuntimeError("a test session is already active")
    REPORT.clear()
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    _temp_owner = tempfile.TemporaryDirectory(prefix="run-", dir=TEMP_ROOT)
    _temp = Path(_temp_owner.name)
    for key in ("MPLCONFIGDIR", "XDG_CACHE_HOME", "ZIG_GLOBAL_CACHE_DIR"):
        _saved_environment[key] = os.environ.get(key)
    os.environ["MPLCONFIGDIR"] = str(_temp / "cache" / "matplotlib")
    os.environ["XDG_CACHE_HOME"] = str(_temp / "cache")
    os.environ["ZIG_GLOBAL_CACHE_DIR"] = str(_temp / "zig-global-cache")
    return _temp


def temp_dir() -> Path:
    if _temp is None:
        return start_session()
    return _temp


def finish_session(success: bool) -> None:
    """Write the report and restore the environment even when reporting fails."""

    global _temp_owner, _temp
    try:
        RESULTS.mkdir(parents=True, exist_ok=True)
        status = "complete" if success else "partial (the test suite failed)"
        SEMANTIC_REPORT.write_text(
            f"Semantic equivalence results\nReport status: {status}\n" + "\n".join(REPORT) + "\n",
            encoding="utf-8",
        )
    finally:
        for key, value in _saved_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        _saved_environment.clear()
        if _temp_owner is not None:
            _temp_owner.cleanup()
        _temp_owner = None
        _temp = None


def fixture(case_dir: Path) -> Path:
    """Return the MLIR input owned by a test case directory."""

    path = case_dir / "input.mlir"
    require(path.is_file(), f"missing test input: {path.relative_to(ROOT)}")
    return path


class TestFailure(AssertionError):
    """A regression check failed."""


class ValidationTest(unittest.TestCase):
    """Base for a file containing one static/dynamic validation test."""

    case_dir: Path

    def test_conversion_and_validation(self) -> None:
        for mode in RESOURCE_MODES:
            with self.subTest(mode=mode):
                output(self.case_dir, mode)


def run(
    command: list[str | Path],
    *,
    env: dict[str, str] | None = None,
    expect_failure: bool = False,
    timeout: float = 300,
) -> subprocess.CompletedProcess[str]:
    """Run a repository command and enforce its expected exit behavior.

    Output is captured to keep successful runs concise. If the command exits
    contrary to ``expect_failure``, both stdout and stderr are included in the
    raised ``TestFailure``.
    """

    rendered = [str(part) for part in command]
    try:
        result = subprocess.run(
            rendered, cwd=ROOT, env=env, text=True, capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise TestFailure(
            f"command timed out after {timeout}s: {shlex.join(rendered)}\n"
            f"{error.stdout or ''}\n{error.stderr or ''}"
        ) from error
    except OSError as error:
        raise TestFailure(f"cannot run {shlex.join(rendered)}: {error}") from error
    if result.returncode < 0:
        raise TestFailure(
            f"command terminated by signal {-result.returncode}: "
            f"{shlex.join(rendered)}\n{result.stdout}\n{result.stderr}"
        )
    failed = result.returncode != 0
    if failed != expect_failure:
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        expectation = "failure" if expect_failure else "success"
        raise TestFailure(
            f"expected {expectation}: {shlex.join(rendered)}\n{output}".rstrip()
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


def verify_qrisp_fixtures(temp: Path) -> None:
    """Regenerate Qrisp fixtures in isolation and reject checked-in drift."""

    generated = temp / "generated-qrisp"
    cache = temp / "cache"
    environment = os.environ.copy()
    environment["MPLCONFIGDIR"] = str(cache / "matplotlib")
    environment["XDG_CACHE_HOME"] = str(cache)
    run([sys.executable, GENERATOR, "--output-dir", generated], env=environment)

    checked_in = {
        path.relative_to(TESTS): path
        for path in TESTS.glob("**/input.mlir")
        if not path.is_relative_to(TEMP_ROOT)
        and (path.parent / "test_case.py").is_file()
        and case_has_qrisp_program(path.parent / "test_case.py")
    }
    fresh = {
        path.relative_to(generated): path for path in generated.rglob("input.mlir")
    }
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
        + ", ".join(map(str, changed))
        + f"; regenerate with {sys.executable} {GENERATOR.relative_to(ROOT)}",
    )
    print(f"PASS Qrisp fixture freshness ({len(fresh)} fixtures)")


def convert_and_validate(fixture: Path, mode: str, temp: Path) -> Path:
    """Convert one fixture, validate its QIR, and return the output path.

    Dynamic mode intentionally omits ``--static`` so the suite also
    protects the driver's documented default. Static mode passes it explicitly.
    """

    require(mode in RESOURCE_MODES, f"invalid resource mode: {mode}")
    work = Path(tempfile.mkdtemp(prefix=f"convert-{fixture.parent.name}-{mode}-", dir=temp))
    output = work / "output.ll"
    command: list[str | Path] = [sys.executable, DRIVER]
    if mode == "static":
        command.extend(["--static"])
    command.extend([fixture, output])
    run(command)
    run([sys.executable, VALIDATOR, output])
    run([OPT, "-passes=verify", "-disable-output", output])
    return output


def output(case_dir: Path, mode: str = "static") -> Path:
    """Convert and validate a case in its own temporary directory."""

    return convert_and_validate(fixture(case_dir), mode, temp_dir())


def load_case(path: Path):
    """Load a colocated test case module without exposing import noise."""

    module_name = "test_case_" + "_".join(path.parent.parts[-2:])
    spec = importlib.util.spec_from_file_location(module_name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(module)
    return module


def case_has_qrisp_program(path: Path) -> bool:
    """Return whether a case module declares a local Qrisp source program."""

    return hasattr(load_case(path), "qrisp_program")


def load_statevector(path: Path) -> dict:
    """Load and validate a state-vector JSON document."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TestFailure(f"cannot read state vector {path}: {error}") from error
    validate_statevector(document, str(path))
    return document


def validate_statevector(document: dict, context: str) -> list[complex]:
    """Reject malformed, non-finite, truncated, or unnormalized simulator output."""

    require(isinstance(document, dict), f"{context}: expected a state-vector object")
    require(document.get("format") == "jasp-to-qir-statevector-v1", f"{context}: bad format")
    qubits = document.get("num_qubits")
    require(type(qubits) is int and qubits >= 0, f"{context}: bad qubit count")
    require(document.get("basis_order") == "qubit 0 is the leftmost (most-significant) bit",
            f"{context}: bad basis order")
    pairs = document.get("amplitudes")
    require(isinstance(pairs, list) and len(pairs) == 1 << qubits,
            f"{context}: state-vector length mismatch")
    values = []
    for index, pair in enumerate(pairs):
        require(isinstance(pair, (list, tuple)) and len(pair) == 2
                and all(type(v) in (int, float) and math.isfinite(v) for v in pair),
                f"{context}: malformed amplitude {index}")
        values.append(complex(*pair))
    norm = sum(abs(value) ** 2 for value in values)
    require(abs(norm - 1) <= STATEVECTOR_TOLERANCE,
            f"{context}: state vector is not normalized (norm squared {norm})")
    return values


def compare_statevectors(expected: dict, actual: dict, case: str, mode: str) -> float:
    """Compare physical states, aligning global phase using their overlap.

    The exporters also canonicalize phase, but selecting the first nonzero
    amplitude is unstable when that amplitude is close to numerical noise.
    """

    context = f"{case} ({mode})"
    expected_values = validate_statevector(expected, context + " Qrisp")
    actual_values = validate_statevector(actual, context + " QIR")
    require(expected["num_qubits"] == actual["num_qubits"],
            f"{context}: qubit-count mismatch")
    overlap = sum(a.conjugate() * b for a, b in zip(expected_values, actual_values))
    phase = overlap / abs(overlap) if abs(overlap) else 1
    maximum_difference = 0.0
    for index, (a, b) in enumerate(zip(expected_values, actual_values)):
        difference = abs(a - b / phase)
        maximum_difference = max(maximum_difference, difference)
        require(difference <= STATEVECTOR_TOLERANCE,
                f"{context}: amplitude {index} differs: Qrisp={a}, QIR={b / phase}")
    return maximum_difference


def remove_zero_suffix_qubits(document: dict, qubits: int, case: str, mode: str) -> dict:
    """Remove unused trailing simulator qubits after verifying they are zero."""

    extra_qubits = document["num_qubits"] - qubits
    if extra_qubits <= 0:
        return document
    stride = 1 << extra_qubits
    amplitudes = document["amplitudes"]
    for index, pair in enumerate(amplitudes):
        if index % stride:
            require(
                abs(complex(*pair)) <= STATEVECTOR_TOLERANCE,
                f"{case} ({mode}): temporary qubit is not zero at amplitude {index}",
            )
    projected = dict(document)
    projected["num_qubits"] = qubits
    projected["qubits"] = document["qubits"][:qubits]
    projected["amplitudes"] = amplitudes[::stride]
    return projected


def report_table(title: str, headings, rows) -> None:
    """Keep semantic values side by side without a separate report data model."""

    rows = [tuple(map(str, headings)), *(tuple(map(str, row)) for row in rows)]
    widths = [max(len(row[i]) for row in rows) for i in range(len(headings))]
    REPORT.extend(["", title])
    REPORT.extend("  ".join(value.ljust(width) for value, width in zip(row, widths))
                  for row in rows)


def verify_statevector_case(
    case_dir: Path,
    qubits: int,
    resource_modes: tuple[str, ...] = RESOURCE_MODES,
) -> None:
    """Compare one unmeasured Qrisp program with validated QIR in each mode."""

    require(bool(resource_modes) and all(mode in RESOURCE_MODES for mode in resource_modes),
            f"invalid resource modes: {resource_modes}")
    case_dir = case_dir.resolve()
    name = str(case_dir.relative_to(TESTS))
    work = Path(tempfile.mkdtemp(prefix="statevector-", dir=temp_dir()))
    expected_path = work / "qrisp.json"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
    run([sys.executable, QRISP_STATEVECTOR, case_dir / "test_case.py",
         "--function", "qrisp_program", "--output", expected_path], env=environment)
    expected = load_statevector(expected_path)
    require(expected["num_qubits"] <= qubits, f"{name}: insufficient simulator capacity")
    vectors = [expected]
    for mode in resource_modes:
        actual_path = work / f"{mode}.json"
        command = [sys.executable, QIR_STATEVECTOR, output(case_dir, mode),
                   "--seed", "7", "--output", actual_path]
        if mode == "dynamic":
            command.extend(["--n-qubits", str(qubits)])
        run(command)
        actual = load_statevector(actual_path)
        require(expected["num_qubits"] <= actual["num_qubits"] <= qubits,
                f"{name} ({mode}): QIR resource-count mismatch")
        actual = remove_zero_suffix_qubits(actual, expected["num_qubits"], name, mode)
        compare_statevectors(expected, actual, name, mode)
        vectors.append(actual)
    report_table(
        f"State vector: {name}", ["basis", "Qrisp", *(f"{m.title()} QIR" for m in resource_modes)],
        [(format(i, f"0{expected['num_qubits']}b"),
          *(f"[{v['amplitudes'][i][0]: .7f}, {v['amplitudes'][i][1]: .7f}]" for v in vectors))
         for i in range(len(expected["amplitudes"]))],
    )


def flatten_tree(value) -> list:
    """Flatten tuple/list result structure while retaining scalar leaves."""

    if isinstance(value, (tuple, list)):
        flattened = []
        for item in value:
            flattened.extend(flatten_tree(item))
        return flattened
    return [value]


def exact_integer(value, context: str) -> int:
    """Do not silently truncate fractional or string simulator outputs."""

    try:
        integer = int(value)
        valid = not isinstance(value, (str, bytes)) and value == integer
    except (TypeError, ValueError, OverflowError):
        valid = False
    require(valid, f"{context}: expected an integer result, got {value!r}")
    return integer


def qrisp_result_bits(result, widths: tuple[int, ...], case: str) -> list[int]:
    """Expand Qrisp result leaves into QubitArray least-significant-bit order."""

    require(all(type(width) is int and width > 0 for width in widths),
            f"{case}: result widths must be positive integers")
    leaves = flatten_tree(result)
    require(
        len(leaves) == len(widths),
        f"{case}: expected {len(widths)} Qrisp result leaves, got {len(leaves)}",
    )
    bits = []
    for value, width in zip(leaves, widths):
        integer = exact_integer(value, case)
        require(0 <= integer < 1 << width, f"{case}: result {integer} exceeds width {width}")
        bits.extend((integer >> index) & 1 for index in range(width))
    return bits


def selene_result_bits(entries, widths: tuple[int, ...], case: str, mode: str) -> list[int]:
    """Decode static scalar records or dynamic buffer/packed-integer records.

    Selene can expose the whole reusable result buffer before its packed
    integer record. Only the measured prefix is meaningful; if both forms
    are present, they must agree. Labels are used only to pair duplicates.
    """

    require(mode in RESOURCE_MODES, f"invalid resource mode: {mode}")
    require(all(type(width) is int and width > 0 for width in widths),
            f"{case}: result widths must be positive integers")
    context = f"{case} ({mode})"
    cursor = 0

    def take():
        nonlocal cursor
        require(cursor < len(entries), f"{context}: missing measurement output")
        label, value = entries[cursor]
        cursor += 1
        return label, [exact_integer(item, context) for item in flatten_tree(value)]

    bits = []
    for width in widths:
        if mode == "dynamic" and width > 1:
            label, values = take()
            if len(values) == 1:
                integer = values[0]
                require(0 <= integer < 1 << width, f"{context}: packed result exceeds width {width}")
                measured = [(integer >> i) & 1 for i in range(width)]
            else:
                require(len(values) >= width and all(v in (0, 1) for v in values),
                        f"{context}: malformed result buffer {values}")
                measured = values[:width]
                if cursor < len(entries) and entries[cursor][0] == label:
                    _, packed = take()
                    require(packed == [sum(bit << i for i, bit in enumerate(measured))],
                            f"{context}: buffer and packed result disagree")
            bits.extend(measured)
        else:
            for _ in range(width):
                _, values = take()
                require(len(values) == 1 and values[0] in (0, 1),
                        f"{context}: expected a scalar bit, got {values}")
                bits.extend(values)
    require(cursor == len(entries), f"{context}: unexpected output records")
    return bits


def verify_measurement_case(
    case_dir: Path,
    function,
    *,
    qubits: int,
    widths: tuple[int, ...],
    expected: tuple[int, ...],
) -> None:
    """Check every deterministic outcome against an independent expected bitstring."""

    from qrisp.jasp import jaspify
    from selene_sim import Quest, build

    case_dir = case_dir.resolve()
    name = str(case_dir.relative_to(TESTS))
    work = Path(tempfile.mkdtemp(prefix="measurement-", dir=temp_dir()))
    with contextlib.redirect_stdout(io.StringIO()):
        result = jaspify(function)()
    qrisp_bits = qrisp_result_bits(result, widths, name)
    require(qrisp_bits == list(expected), f"{name}: Qrisp produced {qrisp_bits}, expected {expected}")
    results = [qrisp_bits]
    for mode in RESOURCE_MODES:
        runner = build(output(case_dir, mode), build_dir=work / mode)
        entries = list(runner.run(simulator=Quest(random_seed=7), n_qubits=qubits))
        bits = selene_result_bits(entries, widths, name, mode)
        require(bits == list(expected), f"{name} ({mode}): QIR produced {bits}, expected {expected}")
        results.append(bits)
    report_table(f"Measurement: {name}", ["Qrisp", "Static QIR", "Dynamic QIR"],
                 [["".join(map(str, bits)) for bits in results]])


def expect_conversion_failure(
    fixture: Path,
    expected: str,
    temp: Path,
    *,
    mode: str,
) -> None:
    """Require conversion to fail cleanly with a specific diagnostic."""

    require(mode in RESOURCE_MODES, f"invalid resource mode: {mode}")
    work = Path(tempfile.mkdtemp(prefix="invalid-", dir=temp))
    output = work / "output.ll"
    command: list[str | Path] = [sys.executable, DRIVER]
    if mode == "static":
        command.extend(["--static"])
    command.extend([fixture, output])
    result = run(command, expect_failure=True)
    require(expected in result.stderr, f"{fixture.name}: missing error {expected!r}")
    require("Traceback" not in result.stderr, f"{fixture.name}: printed a traceback")
