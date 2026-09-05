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
