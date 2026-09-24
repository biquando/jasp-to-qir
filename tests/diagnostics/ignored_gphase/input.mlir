builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = arith.constant dense<1> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %angle = arith.constant dense<0.75> : tensor<f64>
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = jasp.quantum_gate "gphase" (%4, %angle) , %5 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %7 = jasp.quantum_gate "x" (%4) , %6 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    func.return %7 : !jasp.QuantumState
  }
}
