builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QuantumState) {
    %0 = arith.constant dense<3> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = arith.constant dense<1> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = arith.constant dense<4.100000e-01> : tensor<f64>
    %9 = jasp.quantum_gate "ry" (%7, %8) , %5 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %10 = jasp.quantum_gate "s" (%7) , %9 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %11 = arith.constant dense<2> : tensor<i64>
    %12 = jasp.get_qubit %1, %11 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %13 = jasp.quantum_gate "h" (%12) , %10 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %14 = jasp.quantum_gate "cy" (%4, %7) , %13 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %15 = jasp.quantum_gate "cy" (%7, %12) , %14 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %16 = jasp.quantum_gate "cy" (%12, %4) , %15 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    func.return %1, %16 : !jasp.QubitArray, !jasp.QuantumState
  }
}
