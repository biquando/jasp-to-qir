builtin.module @jasp_module {
  func.func private @size() -> tensor<i64>
  func.func public @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %amount = func.call @size() : () -> tensor<i64>
    %qubits, %next = jasp.create_qubits %amount, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %last = jasp.delete_qubits %qubits, %next : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
    func.return %last : !jasp.QuantumState
  }
}
