builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<2> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = jasp.reset %4, %5 : !jasp.Qubit, !jasp.QuantumState -> !jasp.QuantumState
    %7 = arith.constant dense<1> : tensor<i64>
    %8 = jasp.get_qubit %1, %7 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %9 = jasp.quantum_gate "x" (%8) , %6 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %10, %11 = jasp.measure %1, %9 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %10, %11 : tensor<i64>, !jasp.QuantumState
  }
}
