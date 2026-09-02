builtin.module @jasp_module {
  func.func public @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %one = arith.constant dense<1> : tensor<i64>
    %qubits, %next = jasp.create_qubits %one, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %zero = arith.constant dense<0> : tensor<i64>
    %qubit = jasp.get_qubit %qubits, %zero : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %wrong, %last = jasp.measure %qubit, %next : !jasp.Qubit, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %last : !jasp.QuantumState
  }
}
