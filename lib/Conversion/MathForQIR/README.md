# MathForQIR Pass

This pass converts some math-dialect operations before lowering to LLVM-dialect.
It targets operations that would otherwise result in `llvm.intr.*` operations,
which are not supported by QIR.

It performs the following transformations:

## `math.ctpop`

This operation counts the number of set bits in an integer, short for "count
population". By default, this lowers to `llvm.intr.ctpop`, which isn't supported
by QIR.

We convert `math.ctpop` to a series of arith-dialect operations which implement
the SWAR parallel population count algorithm.

## `math.powf(2.0, int)`

Qrisp's QFT generates MLIR code that includes a `math.powf` operations. This
lowers to `llvm.intr.pow` by default, which isn't supported by QIR.

A general implementation in arith-dialect would be complicated, but luckily QFT
only emits the `math.powf` in a specific form:

```
%1 = arith.sitofp %0 : i64 to f64
%2 = arith.constant 2.000000e+00 : f64
%3 = math.powf %2, %1 : f64
```

Thus we just match this pattern and implement it with a left shift and an
int-to-float cast.

To cast, we use `arith.uitofp`, which lowers to `llvm.uitofp`. This operation
isn't explicitly supported in
[QIR 2.1](https://github.com/qir-alliance/qir-spec/blob/2.1/specification/profiles/Adaptive_Profile.md#classical-instructions),
but it was added in the
[latest version](https://github.com/qir-alliance/qir-spec/blob/main/specification/profiles/Adaptive_Profile.md#classical-instructions)
of the spec. It works with Quantinuum's QIR.
