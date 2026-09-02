builtin.module @jasp_module {
  func.func private @make(%state: !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QuantumState) {
    %one = arith.constant dense<1> : tensor<i64>
    %qubits, %next = jasp.create_qubits %one, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    func.return %qubits, %next : !jasp.QubitArray, !jasp.QuantumState
  }
  func.func public @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %qubits, %next = func.call @make(%state) : (!jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QuantumState)
    func.return %next : !jasp.QuantumState
  }
}
