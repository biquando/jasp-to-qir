#!/usr/bin/env python3
"""Prepare Jasp custom assembly for standard MLIR lowering."""

import argparse
import re
from pathlib import Path


STATEMENT_PREFIXES = (
    "%",
    "^",
    "}",
    "arith.",
    "builtin.module",
    "func.",
    "scf.",
    "tensor.",
)

GATE_PATTERN = re.compile(
    r'^(?P<indent>\s*)(?P<results>%[^=]+)=\s*jasp\.quantum_gate\s+"(?P<gate>[^"]+)"\s+'
    r"\((?P<gate_operands>[^)]*)\)\s*,\s*(?P<state>%\w+)\s*:\s*"
    r"\((?P<gate_types>[^)]*)\)\s*,\s*[^-]+->\s*(?P<result_type>.+?)\s*$"
)

OPERATION_PATTERN = re.compile(
    r"^(?P<indent>\s*)(?P<results>(?:%\w+(?:\s*,\s*)?)*)\s*=\s*"
    r"jasp\.(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+"
    r"(?P<operands>.*?)\s*:\s*(?P<input_types>.+?)\s*->\s*"
    r"(?P<result_types>.+?)\s*$"
)


def split_list(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def logical_lines(text: str) -> list[str]:
    """Join arbitrary producer line wraps while retaining MLIR statements."""
    lines: list[str] = []
    for physical_line in text.splitlines():
        stripped = physical_line.strip()
        previous_is_incomplete = lines and lines[-1].rstrip().endswith(
            ("=", ",", "->", ".", "%")
        )
        if lines and (previous_is_incomplete or not stripped.startswith(STATEMENT_PREFIXES)):
            # Producers may wrap in the middle of identifiers, types, or `->`.
            lines[-1] += physical_line.lstrip()
        else:
            lines.append(physical_line)
    return lines


def convert_gate(line: str) -> str | None:
    match = GATE_PATTERN.match(line)
    if not match:
        return None

    operands = split_list(match.group("gate_operands")) + [match.group("state")]
    types = split_list(match.group("gate_types")) + ["!jasp.QuantumState"]
    return (
        f'{match.group("indent")}{match.group("results").strip()} = "jasp.quantum_gate"'
        f'({", ".join(operands)}) {{gate_type = "{match.group("gate")}"}} : '
        f'({", ".join(types)}) -> {match.group("result_type")}'
    )


def convert_operation(line: str) -> str:
    match = OPERATION_PATTERN.match(line)
    if not match:
        return line

    name = match.group("name")
    input_types = split_list(match.group("input_types"))
    if name == "create_qubits":
        input_types.reverse()  # The custom syntax declares state before size.

    result_types = split_list(match.group("result_types"))
    inputs = f'({", ".join(input_types)})'
    results = f'({", ".join(result_types)})' if len(result_types) > 1 else result_types[0]
    operands = ", ".join(split_list(match.group("operands")))
    return (
        f'{match.group("indent")}{match.group("results").strip()} = '
        f'"jasp.{name}"({operands}) : '
        f"{inputs} -> {results}"
    )


def convert_line(line: str) -> str:
    return convert_gate(line) or convert_operation(line)


def replace_ssa_uses(line: str, aliases: dict[str, str]) -> str:
    for old, new in aliases.items():
        line = re.sub(rf"(?<![\w.]){re.escape(old)}(?![\w.])", new, line)
    return line


def prepare_for_lowering(lines: list[str]) -> list[str]:
    """Scalarize rank-0 tensors and replace Jasp types with LLVM-legal types."""
    prepared: list[str] = []
    aliases: dict[str, str] = {}
    in_main = False

    for original in lines:
        if original.lstrip().startswith("func.func"):
            aliases = {}
            in_main = " public @main(" in original

        line = replace_ssa_uses(original, aliases)
        identity = re.match(
            r"^\s*(%\w+)\s*=\s*tensor\.(?:extract\s+(%\w+)\[\]|from_elements\s+(%\w+))",
            line,
        )
        if identity:
            aliases[identity.group(1)] = identity.group(2) or identity.group(3)
            continue

        line = re.sub(
            r"arith\.constant\s+dense<([^>]+)>\s*:\s*tensor<(i1|i64|f64)>",
            r"arith.constant \1 : \2",
            line,
        )
        line = line.replace("tensor<i1>", "i1")
        line = line.replace("tensor<i64>", "i64")
        line = line.replace("tensor<f64>", "f64")
        line = line.replace("!jasp.QuantumState", "i1")
        # Keep both the static resource base and array length available while
        # arrays flow through calls and structured control flow.
        line = line.replace("!jasp.QubitArray", "!llvm.struct<(i64, i64)>")
        line = line.replace("!jasp.Qubit", "!llvm.ptr")

        if in_main and line.lstrip().startswith("func.func"):
            argument = re.search(r"(%\w+): i1", line)
            if not argument:
                raise ValueError("expected the Jasp state argument on @main")
            aliases[argument.group(1)] = "%jasp_state"
            line = re.sub(r"\(%\w+: i1\)", "()", line, count=1)
            line = re.sub(r"->\s*(?:\([^)]*\)|[^\{]+)(?=\s*\{)", "-> i64", line, count=1)
            prepared.append(line)
            prepared.append("    %jasp_state = arith.constant 1 : i1")
            continue

        if in_main and line.lstrip().startswith("func.return"):
            prepared.append("    %jasp_exit = arith.constant 0 : i64")
            prepared.append("    func.return %jasp_exit : i64")
            in_main = False
            continue

        prepared.append(line)

    return prepared


def convert(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    generic = [convert_line(line) for line in logical_lines(source)]
    converted = "\n".join(prepare_for_lowering(generic)) + "\n"
    output_path.write_text(converted, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    convert(args.input, args.output)


if __name__ == "__main__":
    main()
