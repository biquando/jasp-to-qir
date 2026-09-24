builtin.module @jasp_module {
  func.func public @main(%arg3: !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QuantumState) {
    %0 = arith.constant dense<2> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg3 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = arith.constant dense<1> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = jasp.quantum_gate "h" (%7) , %5 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %9 = arith.constant dense<7.500000e-01> : tensor<f64>
    %10 = jasp.quantum_gate "gphase" (%7, %9) , %8 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %11 = func.call @ctrl_env(%4, %1, %10) : (!jasp.Qubit, !jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
    func.return %1, %11 : !jasp.QubitArray, !jasp.QuantumState
  }
  func.func private @ctrl_env(%arg0: !jasp.Qubit, %arg1: !jasp.QubitArray, %arg2: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = arith.constant dense<1> : tensor<i64>
    %1 = jasp.get_qubit %arg1, %0 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %2 = arith.constant dense<5.000000e-01> : tensor<f64>
    %3 = jasp.quantum_gate "p" (%arg0, %2) , %arg2 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    func.return %3 : !jasp.QuantumState
  }
}
