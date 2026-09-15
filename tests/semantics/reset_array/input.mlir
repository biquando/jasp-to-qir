builtin.module @jasp_module {
  func.func public @main(%arg2: !jasp.QuantumState) -> (tensor<i64>, tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<1> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<2> : tensor<i64>
    %4, %5 = jasp.create_qubits %3, %2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %6 = jasp.get_size %1 : !jasp.QubitArray -> tensor<i64>
    %7 = arith.constant 1 : i64
    %8 = tensor.extract %6[] : tensor<i64>
    %9 = arith.subi %8, %7 : i64
    %10 = tensor.from_elements %9 : tensor<i64>
    %11 = arith.subi %9, %9 : i64
    %12 = tensor.from_elements %11 : tensor<i64>
    %13, %14, %15, %16 = scf.while (%arg9 = %1, %arg10 = %10, %arg11 = %12, %arg12 = %5) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %17 = tensor.extract %arg11[] : tensor<i64>
      %18 = tensor.extract %arg10[] : tensor<i64>
      %19 = arith.cmpi sle, %17, %18 : i64
      scf.condition(%19) %arg9, %arg10, %arg11, %arg12 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg3: !jasp.QubitArray, %arg4: tensor<i64>, %arg5: tensor<i64>, %arg6: !jasp.QuantumState):
      %20 = jasp.get_qubit %arg3, %arg5 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %21 = jasp.quantum_gate "x" (%20) , %arg6 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %22 = arith.constant 1 : i64
      %23 = tensor.extract %arg5[] : tensor<i64>
      %24 = arith.addi %23, %22 : i64
      %25 = tensor.from_elements %24 : tensor<i64>
      %26 = func.call @_jrange_marker(%25, %arg4) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg3, %arg4, %26, %21 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %27 = arith.constant dense<0> : tensor<i64>
    %28 = jasp.get_qubit %4, %27 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %29 = jasp.quantum_gate "h" (%28) , %16 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %30 = jasp.get_qubit %4, %0 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %31 = jasp.quantum_gate "cx" (%28, %30) , %29 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %32 = jasp.reset %4, %31 : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
    %33, %34 = jasp.measure %1, %32 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    %35, %36 = jasp.measure %4, %34 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %33, %35, %36 : tensor<i64>, tensor<i64>, !jasp.QuantumState
  }
  func.func private @_jrange_marker(%arg0: tensor<i64>, %arg1: tensor<i64>) -> (tensor<i64>) {
    func.return %arg0 : tensor<i64>
  }
}
