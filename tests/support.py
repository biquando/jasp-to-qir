#!/usr/bin/env python3
"""Shared mechanics for the categorized Jasp-to-QIR tests.

Invoke this file with the repository virtual environment::

    ./venv/bin/python tests/run_tests.py

Test modules contain one test case each and delegate process execution,
conversion caching, and semantic comparison to this module. ``run_tests.py``
is intentionally limited to unittest discovery and suite lifecycle.
"""

from __future__ import annotations

import os
import contextlib
import importlib.util
import io
import json
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
DRIVER = ROOT / "tools/jasp_to_ll.py"
VALIDATOR = ROOT / "tools/validate_qir.py"
GENERATOR = TESTS / "generate_qrisp_fixtures.py"
QRISP_STATEVECTOR = ROOT / "tools/qrisp_statevector.py"
QIR_STATEVECTOR = ROOT / "tools/qir_statevector.py"
LLVM_BIN = Path(os.environ.get("LLVM_BIN", "/opt/homebrew/opt/llvm/bin"))
OPT = LLVM_BIN / "opt"
STATEVECTOR_TOLERANCE = 1e-6
RESOURCE_MODES = ("static", "dynamic")

_temp_owner: tempfile.TemporaryDirectory[str] | None = None
_temp: Path | None = None
_outputs: dict[tuple[str, str], Path] = {}
STATEVECTOR_REPORT: dict = {}
MEASUREMENT_REPORT: dict = {}


def start_session() -> Path:
    """Create the suite's shared temporary directory and simulator caches."""

    global _temp_owner, _temp
    _outputs.clear()
    STATEVECTOR_REPORT.clear()
    MEASUREMENT_REPORT.clear()
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    _temp_owner = tempfile.TemporaryDirectory(prefix="run-", dir=TEMP_ROOT)
    _temp = Path(_temp_owner.name)
    os.environ["MPLCONFIGDIR"] = str(_temp / "cache" / "matplotlib")
    os.environ["XDG_CACHE_HOME"] = str(_temp / "cache")
    os.environ["ZIG_GLOBAL_CACHE_DIR"] = str(_temp / "zig-global-cache")
    return _temp


def temp_dir() -> Path:
    if _temp is None:
        return start_session()
    return _temp


def finish_session(success: bool) -> None:
    """Write completed semantic output and remove the temporary directory."""

    global _temp_owner, _temp
    write_semantic_report(
        STATEVECTOR_REPORT, MEASUREMENT_REPORT, suite_success=success
    )
    if _temp_owner is not None:
        _temp_owner.cleanup()
    _temp_owner = None
    _temp = None
    _outputs.clear()
    if TEMP_ROOT.exists() and not any(TEMP_ROOT.iterdir()):
        TEMP_ROOT.rmdir()


def fixture(case_dir: Path) -> Path:
    """Return the MLIR input owned by a test case directory."""

    path = case_dir / "input.mlir"
    require(path.is_file(), f"missing test input: {path.relative_to(ROOT)}")
    return path


class TestFailure(RuntimeError):
    """A regression check failed."""


class ValidationTest(unittest.TestCase):
    """Base for a file containing one static/dynamic validation test."""

    case_dir: Path

    def test_conversion_and_validation(self) -> None:
        verify_valid_fixture(self.case_dir)


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

    checked_in = {
        path.relative_to(TESTS): path
        for category in ("validation", "statevector", "semantics")
        for path in (TESTS / category).glob("*/input.mlir")
        if (path.parent / "test_case.py").is_file()
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

    Static mode intentionally omits ``--dynamic`` so the suite also
    protects the driver's documented default. Dynamic mode passes it explicitly.
    """

    category, case = fixture.relative_to(TESTS).parts[:2]
    output = temp / f"{category}-{case}.{mode}.ll"
    command: list[str | Path] = [sys.executable, DRIVER]
    if mode == "dynamic":
        command.extend(["--dynamic"])
    command.extend([fixture, output])
    run(command)
    run([sys.executable, VALIDATOR, output])
    run([OPT, "-passes=verify", "-disable-output", output])
    stem = output.with_suffix("")
    for suffix in ("llvm.mlir", "raw.ll"):
        require(not stem.with_suffix(f".{suffix}").exists(), f"unexpected {suffix}")
    return output


def verify_valid_fixture(case_dir: Path) -> None:
    """Convert and validate one fixture in both resource modes."""

    source = fixture(case_dir)
    for mode in ("static", "dynamic"):
        _outputs[(mode, str(case_dir))] = convert_and_validate(source, mode, temp_dir())


def output(case_dir: Path, mode: str = "static") -> Path:
    """Return a validated conversion, creating and caching it when necessary."""

    key = (mode, str(case_dir))
    if key not in _outputs:
        _outputs[key] = convert_and_validate(fixture(case_dir), mode, temp_dir())
    return _outputs[key]


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
    """Load and minimally validate a state-vector JSON document."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TestFailure(f"cannot read state vector {path}: {error}") from error
    require(document.get("format") == "jasp-to-qir-statevector-v1", f"{path}: bad format")
    require(isinstance(document.get("num_qubits"), int), f"{path}: bad qubit count")
    require(isinstance(document.get("amplitudes"), list), f"{path}: bad amplitudes")
    return document


def compare_statevectors(expected: dict, actual: dict, case: str, mode: str) -> float:
    """Compare two normalized dense vectors with a small numerical tolerance."""

    require(
        expected["num_qubits"] == actual["num_qubits"],
        f"{case} ({mode}): qubit-count mismatch",
    )
    require(
        expected.get("basis_order") == actual.get("basis_order"),
        f"{case} ({mode}): basis-order mismatch",
    )
    expected_values = expected["amplitudes"]
    actual_values = actual["amplitudes"]
    require(
        len(expected_values) == len(actual_values),
        f"{case} ({mode}): state-vector length mismatch",
    )
    # Qrisp's simulator may use single-precision kernels for decomposed gates.
    maximum_difference = 0.0
    for index, (expected_pair, actual_pair) in enumerate(
        zip(expected_values, actual_values)
    ):
        require(
            len(expected_pair) == 2 and len(actual_pair) == 2,
            f"{case} ({mode}): malformed amplitude {index}",
        )
        expected_value = complex(*expected_pair)
        actual_value = complex(*actual_pair)
        difference = abs(expected_value - actual_value)
        maximum_difference = max(maximum_difference, difference)
        allowed = STATEVECTOR_TOLERANCE + STATEVECTOR_TOLERANCE * abs(expected_value)
        require(
            difference <= allowed,
            f"{case} ({mode}): amplitude {index} differs: "
            f"Qrisp={expected_value}, QIR={actual_value}",
        )
    return maximum_difference


def amplitudes_by_basis(document: dict) -> dict[str, list[float]]:
    """Label dense amplitudes with their computational-basis strings."""

    width = document["num_qubits"]
    return {
        format(index, f"0{width}b"): pair
        for index, pair in enumerate(document["amplitudes"])
    }


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


def verify_statevectors(
    outputs: dict[tuple[str, str], Path], cases, temp: Path
) -> dict:
    """Compare Qrisp and Selene/QuEST vectors in the requested resource modes."""

    comparisons = 0
    report = {}
    for fixture_name, case in cases.items():
        function_name = case["function"].__name__
        qrisp_output = temp / f"{Path(fixture_name).stem}.qrisp-state.json"
        environment = os.environ.copy()
        python_path = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = str(ROOT) + (os.pathsep + python_path if python_path else "")
        run(
            [
                sys.executable,
                QRISP_STATEVECTOR,
                case["source"],
                "--function",
                function_name,
                "--output",
                qrisp_output,
            ],
            env=environment,
        )
        expected = load_statevector(qrisp_output)
        require(
            expected["num_qubits"] <= case["qubits"],
            f"{fixture_name}: Qrisp requires more than the simulator capacity",
        )
        case_report = {
            "num_qubits": expected["num_qubits"],
            "basis_order": expected["basis_order"],
            "tolerance": STATEVECTOR_TOLERANCE,
            "resource_modes": case["resource_modes"],
        }
        amplitudes = {"qrisp": amplitudes_by_basis(expected)}

        for mode in case["resource_modes"]:
            qir_output = temp / f"{Path(fixture_name).stem}.{mode}.qir-state.json"
            command: list[str | Path] = [
                sys.executable,
                QIR_STATEVECTOR,
                outputs[(mode, fixture_name)],
                "--seed",
                "7",
                "--output",
                qir_output,
            ]
            if mode == "dynamic":
                command.extend(["--n-qubits", str(case["qubits"])])
            run(command)
            actual = load_statevector(qir_output)
            require(
                actual["num_qubits"] == case["qubits"],
                f"{fixture_name} ({mode}): QIR resource-count mismatch",
            )
            actual = remove_zero_suffix_qubits(
                actual, expected["num_qubits"], fixture_name, mode
            )
            maximum_difference = compare_statevectors(
                expected, actual, fixture_name, mode
            )
            amplitudes[f"{mode}_qir"] = amplitudes_by_basis(actual)
            case_report[f"{mode}_max_abs_difference"] = maximum_difference
            comparisons += 1
        case_report["amplitudes"] = {
            basis: {
                source: values[basis]
                for source, values in amplitudes.items()
            }
            for basis in amplitudes["qrisp"]
        }
        report[Path(fixture_name).stem] = case_report
    print(f"PASS state-vector equivalence ({comparisons} comparisons)")
    return report


def verify_statevector_case(
    case_dir: Path,
    qubits: int,
    resource_modes: tuple[str, ...] = RESOURCE_MODES,
) -> None:
    """Run one state-vector case and retain its report entry."""

    require(bool(resource_modes), "a state-vector case must select a resource mode")
    require(
        len(set(resource_modes)) == len(resource_modes)
        and all(mode in RESOURCE_MODES for mode in resource_modes),
        f"invalid resource modes: {resource_modes}",
    )
    name = case_dir.name
    report = verify_statevectors(
        {(mode, name): output(case_dir, mode) for mode in resource_modes},
        {name: {
            "function": load_case(case_dir / "test_case.py").qrisp_program,
            "source": case_dir / "test_case.py",
            "qubits": qubits,
            "resource_modes": resource_modes,
        }},
        temp_dir(),
    )
    STATEVECTOR_REPORT.update(report)


def flatten_tree(value) -> list:
    """Flatten tuple/list result structure while retaining scalar leaves."""

    if isinstance(value, (tuple, list)):
        flattened = []
        for item in value:
            flattened.extend(flatten_tree(item))
        return flattened
    return [value]


def qrisp_result_bits(result, widths: tuple[int, ...], case: str) -> list[int]:
    """Expand Qrisp result leaves into QubitArray least-significant-bit order."""

    leaves = flatten_tree(result)
    require(
        len(leaves) == len(widths),
        f"{case}: expected {len(widths)} Qrisp result leaves, got {len(leaves)}",
    )
    bits = []
    for value, width in zip(leaves, widths):
        integer = int(value)
        require(0 <= integer < 1 << width, f"{case}: result {integer} exceeds width {width}")
        bits.extend((integer >> index) & 1 for index in range(width))
    return bits


def selene_result_bits(
    entries, widths: tuple[int, ...], case: str, mode: str
) -> list[int]:
    """Expand Selene scalar, result-array, and packed-integer records."""

    bits = []
    cursor = 0
    for width in widths:
        require(
            cursor < len(entries),
            f"{case} ({mode}): missing output for width {width}",
        )
        if mode == "dynamic" and width > 1:
            items = flatten_tree(entries[cursor][1])
            cursor += 1
            if len(items) == width:
                values = [int(item) for item in items]
                require(
                    all(bit in (0, 1) for bit in values),
                    f"{case} ({mode}): non-bit result array {values}",
                )
                bits.extend(values)
                continue
            require(
                len(items) == 1,
                f"{case} ({mode}): malformed packed result {items}",
            )
            integer = int(items[0])
            require(
                0 <= integer < 1 << width,
                f"{case} ({mode}): packed result {integer} exceeds width {width}",
            )
            bits.extend((integer >> index) & 1 for index in range(width))
            continue

        for _ in range(width):
            require(
                cursor < len(entries),
                f"{case} ({mode}): incomplete scalar output",
            )
            items = flatten_tree(entries[cursor][1])
            cursor += 1
            require(
                len(items) == 1,
                f"{case} ({mode}): expected a scalar result, got {items}",
            )
            bit = int(items[0])
            require(
                bit in (0, 1),
                f"{case} ({mode}): non-bit Selene result {bit}",
            )
            bits.append(bit)
    require(
        cursor == len(entries),
        f"{case} ({mode}): got {len(entries) - cursor} unexpected output records",
    )
    return bits


def verify_measurements(
    outputs: dict[tuple[str, str], Path], cases, temp: Path
) -> dict:
    """Compare deterministic one-shot Qrisp and Selene measurement results."""

    try:
        from qrisp.jasp import jaspify
        from selene_sim import Quest, build
    except ImportError as error:
        raise TestFailure(f"measurement test dependency is unavailable: {error}") from error

    comparisons = 0
    report = {}
    cache_key = "ZIG_GLOBAL_CACHE_DIR"
    previous_cache = os.environ.get(cache_key)
    os.environ[cache_key] = str(temp / "zig-global-cache")
    try:
        for fixture_name, case in cases.items():
            with contextlib.redirect_stdout(io.StringIO()):
                qrisp_result = jaspify(case["function"])()
            expected = list(case["expected"])
            qrisp_bits = qrisp_result_bits(
                qrisp_result, tuple(case["widths"]), fixture_name
            )
            require(
                qrisp_bits == expected,
                f"{fixture_name}: Qrisp produced {qrisp_bits}, expected {expected}",
            )
            case_report = {
                "bit_order": "measurement emission order; QubitArray values are least-significant-bit first",
                "expected": "".join(str(bit) for bit in expected),
                "qrisp": "".join(str(bit) for bit in qrisp_bits),
            }

            for mode in ("static", "dynamic"):
                build_dir = temp / f"selene-{Path(fixture_name).stem}-{mode}"
                try:
                    runner = build(outputs[(mode, fixture_name)], build_dir=build_dir)
                    entries = list(
                        runner.run(
                            simulator=Quest(random_seed=7),
                            n_qubits=case["qubits"],
                        )
                    )
                except Exception as error:
                    raise TestFailure(
                        f"{fixture_name} ({mode}): Selene execution failed: {error}"
                    ) from error
                qir_bits = selene_result_bits(
                    entries, tuple(case["widths"]), fixture_name, mode
                )
                require(
                    qir_bits == expected,
                    f"{fixture_name} ({mode}): QIR produced {qir_bits}, "
                    f"expected {expected} and Qrisp produced {qrisp_bits}",
                )
                case_report[f"{mode}_qir"] = "".join(
                    str(bit) for bit in qir_bits
                )
                comparisons += 1
            report[Path(fixture_name).stem] = case_report
    finally:
        if previous_cache is None:
            os.environ.pop(cache_key, None)
        else:
            os.environ[cache_key] = previous_cache
    print(f"PASS deterministic measurement equivalence ({comparisons} comparisons)")
    return report


def verify_measurement_case(
    case_dir: Path,
    function,
    *,
    qubits: int,
    widths: tuple[int, ...],
    expected: tuple[int, ...],
) -> None:
    """Run one deterministic measurement case and retain its report entry."""

    name = case_dir.name
    report = verify_measurements(
        {(mode, name): output(case_dir, mode) for mode in ("static", "dynamic")},
        {name: {
            "function": function,
            "qubits": qubits,
            "widths": widths,
            "expected": expected,
        }},
        temp_dir(),
    )
    MEASUREMENT_REPORT.update(report)


def write_semantic_report(
    statevectors: dict, measurements: dict, *, suite_success: bool = True
) -> None:
    """Persist completed semantic values in aligned, human-readable columns."""

    def format_amplitude(pair) -> str:
        return f"[{pair[0]: .7f}, {pair[1]: .7f}]"

    RESULTS.mkdir(parents=True, exist_ok=True)
    status = "complete" if suite_success else "partial (the test suite failed)"
    lines = [
        "Semantic equivalence results",
        "=" * 80,
        f"Report status: {status}",
    ]

    for case, report in statevectors.items():
        modes = report["resource_modes"]
        sources = ("qrisp", *(f"{mode}_qir" for mode in modes))
        headings = ("Qrisp", *(f"{mode.title()} QIR" for mode in modes))
        amplitude_rows = [
            (
                basis,
                *(format_amplitude(amplitudes[source]) for source in sources),
            )
            for basis, amplitudes in report["amplitudes"].items()
        ]
        basis_width = max(len("basis"), *(len(row[0]) for row in amplitude_rows))
        value_width = max(
            *(len(heading) for heading in headings),
            *(len(value) for row in amplitude_rows for value in row[1:]),
        )
        differences = ", ".join(
            f"{mode}={report[f'{mode}_max_abs_difference']:.6g}" for mode in modes
        )
        lines.extend(
            [
                "",
                f"State vector: {case}",
                f"  max |difference|: {differences}",
                f"  {'basis':<{basis_width}}  "
                + "  ".join(f"{heading:<{value_width}}" for heading in headings),
                f"  {'-' * basis_width}  "
                + "  ".join("-" * value_width for _ in headings),
            ]
        )
        lines.extend(
            f"  {row[0]:<{basis_width}}  "
            + "  ".join(f"{value:<{value_width}}" for value in row[1:])
            for row in amplitude_rows
        )

    for case, report in measurements.items():
        values = (report["qrisp"], report["static_qir"], report["dynamic_qir"])
        value_width = max(len("Dynamic QIR"), *(len(value) for value in values))
        lines.extend(
            [
                "",
                f"Measurement: {case}",
                f"  {'Qrisp':<{value_width}}  {'Static QIR':<{value_width}}  Dynamic QIR",
                f"  {'-' * value_width}  {'-' * value_width}  {'-' * value_width}",
                f"  {values[0]:<{value_width}}  {values[1]:<{value_width}}  {values[2]}",
            ]
        )

    SEMANTIC_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE semantic results to {SEMANTIC_REPORT.relative_to(ROOT)}")


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
        command.extend(["--dynamic"])
    command.extend([fixture, output])
    result = run(command, expect_failure=True)
    require(expected in result.stderr, f"{fixture.name}: missing error {expected!r}")
    require("Traceback" not in result.stderr, f"{fixture.name}: printed a traceback")


def verify_intermediates(case_dir: Path, temp: Path) -> None:
    """Verify retained files and LLVM-dialect QIR finalization."""

    output = temp / "kept.ll"
    run(
        [
            sys.executable,
            DRIVER,
            "--keep-intermediates",
            fixture(case_dir),
            output,
        ]
    )
    stem = output.with_suffix("")
    for suffix in ("llvm.mlir", "raw.ll"):
        require(stem.with_suffix(f".{suffix}").is_file(), f"missing kept {suffix}")
    llvm_mlir = require_contains(
        stem.with_suffix(".llvm.mlir"),
        "llvm.call @__quantum__rt__initialize",
        'passthrough = ["entry_point"',
        '["required_num_qubits", "2"]',
        "!llvm.ptr {llvm.writeonly}",
        "!llvm.ptr {llvm.readonly}",
        'passthrough = ["irreversible"]',
    )
    require(
        llvm_mlir.count("llvm.call @__quantum__rt__initialize") == 1,
        "LLVM-dialect main was not initialized exactly once",
    )
    raw = stem.with_suffix(".raw.ll").read_text(encoding="utf-8")
    require(
        raw.count("call void @__quantum__rt__initialize(ptr null)") == 1,
        "raw LLVM main was not initialized exactly once",
    )
    environment = os.environ.copy()
    environment.update({"LLVM_BIN": str(LLVM_BIN), "PATH": ""})
    run(
        [sys.executable, DRIVER, fixture(case_dir), temp / "llvm-bin.ll"],
        env=environment,
    )
    print("PASS --keep-intermediates")
