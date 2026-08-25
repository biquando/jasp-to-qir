#!/usr/bin/env python3
"""Run the complete Jasp-to-QIR regression suite.

Invoke this file with the repository virtual environment::

    ./venv/bin/python tests/run_tests.py

The suite has seven phases:

1. Regenerate Qrisp fixtures and compare them byte-for-byte with the checked-in
   files under ``tests/fixtures/qrisp``.
2. Convert every Qrisp fixture in both static and dynamic resource modes, then
   run the QIR and LLVM validators.
3. Inspect representative LLVM output for semantic properties that structural
   validation alone cannot establish.
4. Compare Qrisp and QIR state vectors for deterministic, unmeasured programs.
5. Compare one-shot Qrisp and QIR outputs for deterministic measured programs.
6. Check diagnostics for invalid or unsupported Jasp input.
7. Verify the driver's ``--keep-intermediates`` contract.

Intermediate files and caches live in a per-run directory beneath the ignored
``tests/.tmp`` directory and are removed automatically. Semantic comparison
values are retained in ``tests/results/semantic_results.txt`` for inspection.
Set ``LLVM_BIN`` to override the default Homebrew LLVM tool directory.
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
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

# Generated inputs and deliberately invalid programs have separate ownership.
FIXTURES = TESTS / "fixtures"
QRISP = FIXTURES / "qrisp"
INVALID = FIXTURES / "invalid"
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

    Static mode intentionally omits ``--dynamic`` so the suite also
    protects the driver's documented default. Dynamic mode passes it explicitly.
    """

    category = fixture.parent.name
    output = temp / f"{category}-{fixture.stem}.{mode}.ll"
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
        outputs[("static", "loop.mlir")], '!"backwards_branching", i2 3'
    )
    require_contains(
        outputs[("static", "many_results.mlir")],
        '@label10 = internal constant [10 x i8] c"result_10\\00"',
    )
    require_contains(
        outputs[("static", "statevector_tfim.mlir")],
        "define void @conjugation_env({ i64, i64 } %0)",
    )
    reset = require_contains(
        outputs[("static", "reset_array.mlir")],
        "declare void @__quantum__qis__reset__body(ptr)",
    )
    require(
        "__quantum__qis__reset__body({" not in reset
        and "declare void @__quantum__qis__reset__body(ptr) #" not in reset,
        "reset has an array parameter or function attributes",
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
    before_branch, after_branch = dynamic_conditional.split("br i1", 1)
    require(
        before_branch.count("call ptr @__quantum__rt__result_allocate") == 2
        and after_branch.count("call void @__quantum__rt__result_release") == 2,
        "conditional result lifetime is not balanced across both branches",
    )
    require_adjacent(
        dynamic_conditional,
        "call void @__quantum__qis__mz__body",
        "call void @__quantum__rt__result_record_output",
        2,
    )
    print("PASS focused QIR semantics")


def load_qrisp_cases():
    """Load the Qrisp source functions and semantic case metadata."""

    spec = importlib.util.spec_from_file_location("qrisp_fixture_generator", GENERATOR)
    require(spec is not None and spec.loader is not None, "cannot load fixture generator")
    module = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(module)
    return module


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


def verify_statevectors(
    outputs: dict[tuple[str, str], Path], cases, temp: Path
) -> dict:
    """Compare Qrisp and Selene/QuEST vectors in both resource modes."""

    comparisons = 0
    report = {}
    for fixture_name, case in cases.items():
        function_name = case["function"].__name__
        qrisp_output = temp / f"{Path(fixture_name).stem}.qrisp-state.json"
        run(
            [
                sys.executable,
                QRISP_STATEVECTOR,
                GENERATOR,
                "--function",
                function_name,
                "--output",
                qrisp_output,
            ]
        )
        expected = load_statevector(qrisp_output)
        require(
            expected["num_qubits"] == case["qubits"],
            f"{fixture_name}: Qrisp returned an unexpected qubit count",
        )
        case_report = {
            "num_qubits": expected["num_qubits"],
            "basis_order": expected["basis_order"],
            "tolerance": STATEVECTOR_TOLERANCE,
        }
        amplitudes = {"qrisp": amplitudes_by_basis(expected)}

        for mode in ("static", "dynamic"):
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


def selene_result_bits(entries, case: str, mode: str) -> list[int]:
    """Flatten Selene scalar and result-array records in emission order."""

    bits = []
    for _, value in entries:
        for item in flatten_tree(value):
            bit = int(item)
            require(bit in (0, 1), f"{case} ({mode}): non-bit Selene result {item}")
            bits.append(bit)
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
                qir_bits = selene_result_bits(entries, fixture_name, mode)
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


def write_semantic_report(statevectors: dict, measurements: dict) -> None:
    """Persist successful semantic values in aligned, human-readable columns."""

    def format_amplitude(pair) -> str:
        return f"[{pair[0]: .7f}, {pair[1]: .7f}]"

    RESULTS.mkdir(parents=True, exist_ok=True)
    lines = ["Semantic equivalence results", "=" * 80]

    for case, report in statevectors.items():
        amplitude_rows = [
            (
                basis,
                format_amplitude(amplitudes["qrisp"]),
                format_amplitude(amplitudes["static_qir"]),
                format_amplitude(amplitudes["dynamic_qir"]),
            )
            for basis, amplitudes in report["amplitudes"].items()
        ]
        basis_width = max(len("basis"), *(len(row[0]) for row in amplitude_rows))
        value_width = max(
            len("Dynamic QIR"),
            *(len(value) for row in amplitude_rows for value in row[1:]),
        )
        lines.extend(
            [
                "",
                f"State vector: {case}",
                f"  max |difference|: static={report['static_max_abs_difference']:.6g}, "
                f"dynamic={report['dynamic_max_abs_difference']:.6g}",
                f"  {'basis':<{basis_width}}  {'Qrisp':<{value_width}}  "
                f"{'Static QIR':<{value_width}}  Dynamic QIR",
                f"  {'-' * basis_width}  {'-' * value_width}  "
                f"{'-' * value_width}  {'-' * value_width}",
            ]
        )
        lines.extend(
            f"  {basis:<{basis_width}}  {qrisp:<{value_width}}  "
            f"{static:<{value_width}}  {dynamic}"
            for basis, qrisp, static, dynamic in amplitude_rows
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
    print(f"PASS semantic results written to {SEMANTIC_REPORT.relative_to(ROOT)}")


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
    """Verify retained files and LLVM-dialect QIR finalization."""

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
        [sys.executable, DRIVER, QRISP / "basic.mlir", temp / "llvm-bin.ll"],
        env=environment,
    )
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
            cache_environment = {
                "MPLCONFIGDIR": str(temp / "semantic-cache" / "matplotlib"),
                "XDG_CACHE_HOME": str(temp / "semantic-cache"),
            }
            previous_cache = {
                key: os.environ.get(key) for key in cache_environment
            }
            os.environ.update(cache_environment)
            try:
                cases = load_qrisp_cases()
                statevector_report = verify_statevectors(
                    outputs, cases.STATEVECTOR_CASES, temp
                )
                measurement_report = verify_measurements(
                    outputs, cases.MEASUREMENT_CASES, temp
                )
                write_semantic_report(statevector_report, measurement_report)
            finally:
                for key, value in previous_cache.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
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
