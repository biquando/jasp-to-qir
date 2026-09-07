module @jasp_module {
  func.func @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %size = arith.constant dense<2> : tensor<i64>
    %zero = arith.constant dense<0> : tensor<i64>
    %one = arith.constant dense<1> : tensor<i64>
    %qs, %s0 = jasp.create_qubits %size, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %q0 = jasp.get_qubit %qs, %zero : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %q1 = jasp.get_qubit %qs, %one : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %m0, %s1 = jasp.measure %q0, %s0 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %s2 = jasp.quantum_gate "x" (%q0), %s1 : (!jasp.Qubit), !jasp.QuantumState -> !jasp.QuantumState
    %m1, %s3 = jasp.measure %q0, %s2 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %m2, %s4 = jasp.measure %qs, %s3 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    %s5 = jasp.quantum_gate "x" (%q0), %s4 : (!jasp.Qubit), !jasp.QuantumState -> !jasp.QuantumState
    %s6 = jasp.quantum_gate "x" (%q1), %s5 : (!jasp.Qubit), !jasp.QuantumState -> !jasp.QuantumState
    %m3, %s7 = jasp.measure %qs, %s6 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %s7 : !jasp.QuantumState
  }
}
