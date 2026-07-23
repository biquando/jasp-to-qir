#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
llvm_bin=${LLVM_BIN:-/opt/homebrew/opt/llvm/bin}
temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT

for input in "$root"/tests/*.mlir; do
    name=$(basename "${input%.mlir}")
    output="$temp_dir/$name.ll"
    "$root/venv/bin/python" "$root/tools/jasp_to_ll.py" "$input" "$output"
    "$root/venv/bin/python" "$root/tools/validate_qir.py" "$output"
    "$llvm_bin/opt" -passes=verify -disable-output "$output"
    for suffix in generic.mlir qir.mlir llvm.mlir raw.ll; do
        test ! -e "$temp_dir/$name.$suffix"
    done
    echo "PASS $(basename "$input")"
done

grep -q 'br i1' "$temp_dir/qrisp_adaptive.ll"
grep -q '!"backwards_branching", i2 1' "$temp_dir/qrisp_loop.ll"
grep -q '@label10 = internal constant \[7 x i8\] c"bit_10\\00"' \
    "$temp_dir/qrisp_many_results.ll"
grep -q 'declare void @__quantum__qis__reset__body(ptr) #1' \
    "$temp_dir/qrisp_reset_array.ll"
if grep -q '__quantum__qis__reset__body({' "$temp_dir/qrisp_reset_array.ll"; then
    echo "FAIL qrisp_reset_array.mlir: reset uses an array descriptor" >&2
    exit 1
fi
awk '
    /call void @__quantum__qis__mz__body/ { measurement = NR }
    /call void @__quantum__rt__result_record_output/ {
        if (NR == measurement + 1) adjacent++
    }
    END { exit adjacent == 2 ? 0 : 1 }
' "$temp_dir/qrisp_conditional_measurement.ll"

invalid_template="$root/tests/invalid/unsupported_gate.mlir"
for gate in p gphase unknown_gate; do
    invalid="$temp_dir/invalid_$gate.mlir"
    sed "s/\"p\"/\"$gate\"/" "$invalid_template" >"$invalid"
    if "$root/venv/bin/python" "$root/tools/jasp_to_ll.py" \
        "$invalid" "$temp_dir/unsupported.ll" \
        >"$temp_dir/unsupported.stdout" 2>"$temp_dir/unsupported.stderr"; then
        echo "FAIL $gate: conversion unexpectedly succeeded" >&2
        exit 1
    fi
    grep -q "unsupported Jasp gate '$gate'" "$temp_dir/unsupported.stderr"
    if grep -q "Traceback" "$temp_dir/unsupported.stderr"; then
        echo "FAIL $gate: Python traceback was printed" >&2
        exit 1
    fi
    echo "PASS unsupported gate $gate (expected failure)"
done

kept="$temp_dir/kept.ll"
"$root/venv/bin/python" "$root/tools/jasp_to_ll.py" --keep-intermediates \
    "$root/tests/main.mlir" "$kept"
for suffix in generic.mlir qir.mlir llvm.mlir raw.ll; do
    test -f "$temp_dir/kept.$suffix"
done
echo "PASS --keep-intermediates"
