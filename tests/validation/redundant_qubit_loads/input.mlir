module @jasp_module {
  func.func @main(%state: !jasp.QuantumState) -> (tensor<i1>, !jasp.QuantumState) {
    %size = arith.constant dense<2> : tensor<i64>
    %zero = arith.constant dense<0> : tensor<i64>
    %one = arith.constant dense<1> : tensor<i64>
    %angle = arith.constant dense<0.25> : tensor<f64>
    %qs, %s0 = jasp.create_qubits %size, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %q0 = jasp.get_qubit %qs, %zero : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %q1 = jasp.get_qubit %qs, %one : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %s1 = jasp.quantum_gate "cx" (%q0, %q1), %s0 : (!jasp.Qubit, !jasp.Qubit), !jasp.QuantumState -> !jasp.QuantumState
    %q1_again = jasp.get_qubit %qs, %one : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %s2 = jasp.quantum_gate "rz" (%q1_again, %angle), %s1 : (!jasp.Qubit, tensor<f64>), !jasp.QuantumState -> !jasp.QuantumState
    %q0_again = jasp.get_qubit %qs, %zero : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %q1_last = jasp.get_qubit %qs, %one : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %s3 = jasp.quantum_gate "cx" (%q0_again, %q1_last), %s2 : (!jasp.Qubit, !jasp.Qubit), !jasp.QuantumState -> !jasp.QuantumState
    %s4 = jasp.reset %q0_again, %s3 : !jasp.Qubit, !jasp.QuantumState -> !jasp.QuantumState
    %q0_last = jasp.get_qubit %qs, %zero : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %s5 = jasp.quantum_gate "x" (%q0_last), %s4 : (!jasp.Qubit), !jasp.QuantumState -> !jasp.QuantumState
    %bit, %s6 = jasp.measure %q0_last, %s5 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    func.return %bit, %s6 : tensor<i1>, !jasp.QuantumState
  }
}
