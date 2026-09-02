builtin.module @jasp_module {
  func.func public @main(%arg2: !jasp.QuantumState) -> (tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<3> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = jasp.get_size %1 : !jasp.QubitArray -> tensor<i64>
    %4 = arith.constant 1 : i64
    %5 = tensor.extract %3[] : tensor<i64>
    %6 = arith.subi %5, %4 : i64
    %7 = tensor.from_elements %6 : tensor<i64>
    %8 = arith.subi %6, %6 : i64
    %9 = tensor.from_elements %8 : tensor<i64>
    %10, %11, %12, %13 = scf.while (%arg9 = %1, %arg10 = %7, %arg11 = %9, %arg12 = %2) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %14 = tensor.extract %arg11[] : tensor<i64>
      %15 = tensor.extract %arg10[] : tensor<i64>
      %16 = arith.cmpi sle, %14, %15 : i64
      scf.condition(%16) %arg9, %arg10, %arg11, %arg12 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg3: !jasp.QubitArray, %arg4: tensor<i64>, %arg5: tensor<i64>, %arg6: !jasp.QuantumState):
      %17 = jasp.get_qubit %arg3, %arg5 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %18 = jasp.quantum_gate "h" (%17) , %arg6 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %19 = arith.constant 1 : i64
      %20 = tensor.extract %arg5[] : tensor<i64>
      %21 = arith.addi %20, %19 : i64
      %22 = tensor.from_elements %21 : tensor<i64>
      %23 = func.call @_jrange_marker(%22, %arg4) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg3, %arg4, %23, %18 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %24, %25 = jasp.measure %1, %13 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %24, %25 : tensor<i64>, !jasp.QuantumState
  }
  func.func private @_jrange_marker(%arg0: tensor<i64>, %arg1: tensor<i64>) -> (tensor<i64>) {
    func.return %arg0 : tensor<i64>
  }
}
