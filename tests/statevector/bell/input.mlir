builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QuantumState) {
    %0 = arith.constant dense<2> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = arith.constant dense<1> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = jasp.quantum_gate "cx" (%4, %7) , %5 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    func.return %1, %8 : !jasp.QubitArray, !jasp.QuantumState
  }
}
