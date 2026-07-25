builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i1>, tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<2> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<1> : tensor<i64>
    %4, %5 = jasp.create_qubits %3, %2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %6 = arith.constant dense<0> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = jasp.quantum_gate "h" (%7) , %5 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %9 = jasp.get_qubit %4, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %10 = jasp.quantum_gate "h" (%9) , %8 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %11, %12 = jasp.measure %9, %10 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %13 = tensor.extract %11[] : tensor<i1>
    %14 = arith.constant true
    %15 = arith.xori %13, %14 : i1
    %16 = scf.if %15 -> (!jasp.QuantumState) {
      %17 = arith.constant dense<1> : tensor<i64>
      %18 = jasp.get_qubit %1, %17 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %19 = jasp.quantum_gate "z" (%18) , %12 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %19 : !jasp.QuantumState
    } else {
      %20 = arith.constant dense<1> : tensor<i64>
      %21 = jasp.get_qubit %1, %20 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %22 = jasp.quantum_gate "x" (%21) , %12 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %22 : !jasp.QuantumState
    }
    %23, %24 = jasp.measure %1, %16 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %11, %23, %24 : tensor<i1>, tensor<i64>, !jasp.QuantumState
  }
}
