builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i1>, !jasp.QuantumState) {
    %0 = arith.constant dense<2> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6, %7 = jasp.measure %4, %5 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %8 = tensor.extract %6[] : tensor<i1>
    %9 = arith.constant true
    %10 = arith.xori %8, %9 : i1
    %11 = scf.if %10 -> (!jasp.QuantumState) {
      scf.yield %7 : !jasp.QuantumState
    } else {
      %12 = arith.constant dense<1> : tensor<i64>
      %13 = jasp.get_qubit %1, %12 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %14, %15 = jasp.measure %13, %7 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
      scf.yield %15 : !jasp.QuantumState
    }
    func.return %6, %11 : tensor<i1>, !jasp.QuantumState
  }
}
