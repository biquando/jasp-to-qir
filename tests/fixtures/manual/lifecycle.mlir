builtin.module @jasp_module {
  func.func public @main(%state: !jasp.QuantumState) -> (tensor<i1>, !jasp.QuantumState) {
    %kernel = jasp.create_quantum_kernel -> !jasp.QuantumState
    %one = arith.constant dense<1> : tensor<i64>
    %qubits, %allocated = jasp.create_qubits %one, %kernel : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %deleted = jasp.delete_qubits %qubits, %allocated : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
    %success = jasp.consume_quantum_kernel %deleted : !jasp.QuantumState -> tensor<i1>
    func.return %success, %deleted : tensor<i1>, !jasp.QuantumState
  }
}
