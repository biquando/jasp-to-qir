builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i64>, tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<2> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6, %7, %8, %9 = scf.while (%arg12 = %1, %arg13 = %3, %arg14 = %3, %arg15 = %5) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %10 = arith.constant 2 : i64
      %11 = tensor.extract %arg13[] : tensor<i64>
      %12 = arith.cmpi slt, %11, %10 : i64
      scf.condition(%12) %arg12, %arg13, %arg14, %arg15 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg1: !jasp.QubitArray, %arg2: tensor<i64>, %arg3: tensor<i64>, %arg4: !jasp.QuantumState):
      %13 = arith.constant dense<0> : tensor<i64>
      %14 = jasp.get_qubit %arg1, %13 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %15 = arith.constant dense<1> : tensor<i64>
      %16 = jasp.get_qubit %arg1, %15 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %17 = jasp.quantum_gate "cx" (%14, %16) , %arg4 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %18 = jasp.get_qubit %arg1, %arg2 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %19, %20 = jasp.measure %18, %17 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
      %21 = tensor.extract %19[] : tensor<i1>
      %22 = arith.extui %21 : i1 to i64
      %23 = tensor.extract %arg3[] : tensor<i64>
      %24 = arith.addi %23, %22 : i64
      %25 = tensor.from_elements %24 : tensor<i64>
      %26 = arith.constant 1 : i64
      %27 = tensor.extract %arg2[] : tensor<i64>
      %28 = arith.addi %27, %26 : i64
      %29 = tensor.from_elements %28 : tensor<i64>
      scf.yield %arg1, %29, %25, %20 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %30, %31 = jasp.measure %1, %9 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %8, %30, %31 : tensor<i64>, tensor<i64>, !jasp.QuantumState
  }
}