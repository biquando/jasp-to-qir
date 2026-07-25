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
    for suffix in llvm.mlir raw.ll; do
        test ! -e "$temp_dir/$name.$suffix"
    done
    echo "PASS $(basename "$input")"
done

explicit_static="$temp_dir/main.explicit-static.ll"
"$root/venv/bin/python" "$root/tools/jasp_to_ll.py" \
    --resource-management static "$root/tests/main.mlir" "$explicit_static"
cmp "$temp_dir/main.ll" "$explicit_static"
echo "PASS explicit static resource management"

for input in "$root"/tests/*.mlir; do
    name=$(basename "${input%.mlir}")
    output="$temp_dir/$name.dynamic.ll"
    "$root/venv/bin/python" "$root/tools/jasp_to_ll.py" \
        --resource-management dynamic "$input" "$output"
    "$root/venv/bin/python" "$root/tools/validate_qir.py" "$output"
    "$llvm_bin/opt" -passes=verify -disable-output "$output"
    echo "PASS dynamic $(basename "$input")"
done

dynamic_main="$temp_dir/main.dynamic.ll"
grep -q '!"dynamic_qubit_management", i1 true' "$dynamic_main"
grep -q '!"dynamic_result_management", i1 true' "$dynamic_main"
grep -q '!"arrays", i1 true' "$dynamic_main"
grep -q '__quantum__rt__qubit_array_allocate(i64 2' "$dynamic_main"
grep -q '__quantum__rt__result_array_allocate(i64 2' "$dynamic_main"
grep -q '__quantum__rt__result_array_record_output(i64 2' "$dynamic_main"
grep -q '__quantum__rt__result_array_release(i64 2' "$dynamic_main"
if grep -q 'required_num_\|inttoptr' "$dynamic_main"; then
    echo "FAIL dynamic main: static resource metadata or handles remain" >&2
    exit 1
fi

dynamic_lifecycle="$temp_dir/jasp_lifecycle.dynamic.ll"
grep -q '__quantum__rt__qubit_array_allocate(i64 1' "$dynamic_lifecycle"
grep -q '__quantum__rt__qubit_array_release(i64 1' "$dynamic_lifecycle"

dynamic_conditional="$temp_dir/qrisp_conditional_measurement.dynamic.ll"
test "$(grep -c 'call ptr @__quantum__rt__result_allocate(ptr null)' \
    "$dynamic_conditional")" -eq 2
test "$(grep -c '^  call void @__quantum__rt__result_release' \
    "$dynamic_conditional")" -eq 2
awk '
    /call void @__quantum__qis__mz__body/ { measurement = NR }
    /call void @__quantum__rt__result_record_output/ {
        if (NR == measurement + 1) adjacent++
    }
    END { exit adjacent == 2 ? 0 : 1 }
' "$dynamic_conditional"

for operation in slice fuse parity; do
    input="$root/tests/invalid/unsupported_$operation.mlir"
    if "$root/venv/bin/python" "$root/tools/jasp_to_ll.py" \
        "$input" "$temp_dir/unsupported_$operation.ll" \
        >"$temp_dir/unsupported_$operation.stdout" \
        2>"$temp_dir/unsupported_$operation.stderr"; then
        echo "FAIL $operation: conversion unexpectedly succeeded" >&2
        exit 1
    fi
    grep -q "Unsupported Jasp operation 'jasp.$operation'" \
        "$temp_dir/unsupported_$operation.stderr"
    echo "PASS unsupported operation $operation (expected failure)"
done

if "$root/venv/bin/python" "$root/tools/jasp_to_ll.py" \
    "$root/tests/invalid/dynamic_allocation.mlir" "$temp_dir/dynamic.ll" \
    >"$temp_dir/dynamic.stdout" 2>"$temp_dir/dynamic.stderr"; then
    echo "FAIL dynamic allocation: conversion unexpectedly succeeded" >&2
    exit 1
fi
grep -q 'QIR array backing storage requires a compile-time constant size' \
    "$temp_dir/dynamic.stderr"
echo "PASS dynamic allocation (expected failure)"

if "$root/venv/bin/python" "$root/tools/jasp_to_ll.py" \
    --resource-management dynamic "$root/tests/invalid/dynamic_allocation.mlir" \
    "$temp_dir/runtime-sized.dynamic.ll" \
    >"$temp_dir/runtime-sized.dynamic.stdout" \
    2>"$temp_dir/runtime-sized.dynamic.stderr"; then
    echo "FAIL runtime-sized dynamic array: conversion unexpectedly succeeded" >&2
    exit 1
fi
grep -q 'QIR array backing storage requires a compile-time constant size' \
    "$temp_dir/runtime-sized.dynamic.stderr"
echo "PASS runtime-sized dynamic array (expected failure)"

if "$root/venv/bin/python" "$root/tools/jasp_to_ll.py" \
    "$root/tests/invalid/invalid_measure.mlir" "$temp_dir/invalid_measure.ll" \
    >"$temp_dir/invalid_measure.stdout" 2>"$temp_dir/invalid_measure.stderr"; then
    echo "FAIL invalid measure: conversion unexpectedly succeeded" >&2
    exit 1
fi
grep -q 'requires result type.*tensor<i1>.*operand type.*!jasp.Qubit' \
    "$temp_dir/invalid_measure.stderr"
echo "PASS invalid measure type (expected failure)"

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
    grep -q "Unsupported Jasp gate '$gate'" "$temp_dir/unsupported.stderr"
    if grep -q "Traceback" "$temp_dir/unsupported.stderr"; then
        echo "FAIL $gate: Python traceback was printed" >&2
        exit 1
    fi
    echo "PASS unsupported gate $gate (expected failure)"
done

kept="$temp_dir/kept.ll"
"$root/venv/bin/python" "$root/tools/jasp_to_ll.py" --keep-intermediates \
    "$root/tests/main.mlir" "$kept"
for suffix in llvm.mlir raw.ll; do
    test -f "$temp_dir/kept.$suffix"
done
echo "PASS --keep-intermediates"
