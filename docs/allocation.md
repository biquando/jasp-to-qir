# Dynamic Qubit Allocation

Problem: Jasp/MLIR allows allocation of dynamically-sized qubit arrays, but QIR
does not support this. Specifically, the backing LLVM array of qubit ptrs can be
allocated with any size, but `__quantum__rt__qubit_array_allocate` only supports
a constant size.

Solution: For each qubit array allocation, instead do a bunch of single-qubit
allocations in a for loop. The backing array can be allocated with a dynamic
size on-the-spot, with the for loop of allocations right after it.

## Details

1. `jasp.create_qubits(n)` allocates exactly `n` qubits through repeated calls
   to `__quantum__rt__qubit_allocate`.
2. The returned qubit pointers are stored in a runtime-sized LLVM stack buffer
   created with `alloca ptr, i64 %n`.
3. Results use compile-time-sized `[N x ptr]` buffers, where `N` is configurable
   and defaults to 64. This is required because results must be allocated in the
   QIR entry point's entry block, which means we can't use the same for-loop
   allocation as with the qubits.

## LLVM Representation

Qubit arrays are represented by the allocated buffer and the length.

```
QubitArray {
    ptr data;    // allocated qubit ptr array
    i64 length;  // number of qubits
}
```

Ownership does not need to be tracked, even with fuse/slice, because Jasp
provides explicit deletion calls.

## Qubit creation

For a runtime size `%n`, `jasp.create_qubits(n)` is lowered approximately as
follows (in LLVM pseudocode):

```llvm
%slots = alloca ptr, i64 %n, align 8

; for i = 0; i < n; ++i
%qubit = call ptr @__quantum__rt__qubit_allocate(ptr null)
%slot = getelementptr inbounds ptr, ptr %slots, i64 %i
store ptr %qubit, ptr %slot, align 8

; Construct the QubitArray
%a0 = insertvalue { ptr, i64 } undef, ptr %slots, 0
%array = insertvalue { ptr, i64 } %a0, i64 %n, 1
```

## Qubit access

For a qubit array `%array` and index `%i`, `jasp.get_qubit(array, i)` is lowered
approximately as follows (in LLVM pseudocode):

```llvm
%slot = getelementptr inbounds ptr, ptr %array.data, i64 %i
%qubit = load ptr, ptr %slot, align 8
```

## Qubit deletion

For a qubit array `%array`, `jasp.delete_qubits(array)` is lowered approximately
as follows (in LLVM pseudocode):

```llvm
; for i = 0; i < array.length; ++i
%slot = getelementptr inbounds ptr, ptr %array.data, i64 %i
%qubit = load ptr, ptr %slot, align 8
call void @__quantum__rt__qubit_release(ptr %qubit)
```

## Array slicing and fusing

`jasp.slice` creates a new QubitArray object as follows:

```
slice.data   = array.data + start
slice.length = max(end - start, 0)
```

Slicing also needs to handle Python-like negative indices.

Note that this is a view of the original array, sharing some elements (qubit
ptrs) with the original array.

`jasp.fuse` combines two QubitArrays into a new one:

```
fused.length = left.length + right.length
fused.data   = alloca ptr, fused.length
copy left.data[0:left.length] into fused.data
copy right.data[0:right.length] into fused.data + left.length
```

Again, this is a new, real qubit array. Fuse also needs to handle combining
scalar qubits.

## Result allocation/deletion

The result buffer is compile-time-sized and allocated at the entry block of the
QIR entry point. Here we use length-64, but it should be compile-time
configurable:

```llvm
%results = alloca [64 x ptr], i64 1, align 8
call void @__quantum__rt__result_array_allocate(i64 64, ptr %results, ptr null)
```

Deletion is simple, and is inserted at the return points of the entry point:
```llvm
call void @__quantum__rt__result_array_release(i64 64, ptr %results)
```

One pair of allocate/delete is required for the module. The buffer address is
made available to helper functions. Each measurement result is immediately
read and copied into an `i64`, after which the packed integer is recorded as
output. This means all measurements can reuse the same results buffer.

## Measurement

QIR requires measuring a single qubit at a time into the allocated result slots.

```llvm
; for i = 0; i < array.length; ++i
%qubit_slot = getelementptr inbounds ptr, ptr %array.data, i64 %i
%qubit = load ptr, ptr %qubit_slot, align 8
%result_slot = getelementptr inbounds ptr, ptr %results.data, i64 %i
%result = load ptr, ptr %result_slot, align 8
call void @__quantum__qis__mz__body(%qubit, %result)

; for i = 0; i < array.length; ++i
%bit = call i1 @__quantum__rt__read_result(ptr %result)
%bit_i64 = zext i1 %bit to i64
%shifted = shl i64 %bit_i64, %i
%packed_next = or i64 %packed, %shifted
```

The loop accumulator starts at zero and becomes the Jasp measurement result.
Qubit-array results are packed least-significant-bit first, so the measurement
of qubit `i` is stored in bit `i`. After the loop, record the packed value with
a stable label for the lexical measurement:

```llvm
call void @__quantum__rt__int_record_output(i64 %packed, ptr @result_n)
```

Scalar measurement uses one result slot and returns the `i1` produced by
`__quantum__rt__read_result`; it can be zero-extended when an integer output
record is required.

## Reset

Reset is straightforward; it just needs to be able to handle both scalar and
array arguments.

## Metadata

This requires `dynamic_qubit_management`, `dynamic_result_management`, `arrays`,
and `int_computations` containing i64.

It also requires the `backwards_branching` QIR capability because every
allocation creates a for loop.

## Limitations

1. **Returning qubits**: The main limitation of this method is when functions
   return qubits. Since the backing storage of a qubit array is stack-allocated,
   it's impossible to return a qubit array from a function. This should be
   detected by the compiler and reported as an error. In the future, we could
   inline functions that return qubits, but this doesn't work generally because
   of recursion.

2. **QIR portability**: `alloca ptr, i64 %n` is supported in Quantinuum's QIR,
   but it's not necessarily supported in every QIR backend.

3. **Stack growth**: We allocate a qubit ptr buffer on every
   `jasp.create_qubits`. If this happens inside of a loop, the stack could grow
   for each iteration, even if the qubits are deleted at the end of the loop.
   This is because the stack `alloca`s are never deallocated. It might be
   possible to use `stacksave`/`stackrestore`, but this introduces some
   complexity and might not be supported.

4. **Performance**: Each allocation/deletion requires a for loop, which might be
   slow.

5. **Measurements are statically bounded**: The user must specify a compile-time
   result buffer size. In practice, 64 is a good maximum because jasp stores
   measurement results as a 64-bit integer anyway.
