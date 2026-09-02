builtin.module @jasp_module {
  func.func private @size() -> tensor<i64>
  func.func public @main(%state: !jasp.QuantumState) -> (tensor<i64>, !jasp.QuantumState) {
    %amount = func.call @size() : () -> tensor<i64>
    %qubits, %next = jasp.create_qubits %amount, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %result, %last = jasp.measure %qubits, %next : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %result, %last : tensor<i64>, !jasp.QuantumState
  }
}
