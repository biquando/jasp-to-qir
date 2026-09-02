builtin.module @jasp_module {
  func.func public @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %one = arith.constant dense<1> : tensor<i64>
    %left, %next = jasp.create_qubits %one, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %right, %last = jasp.create_qubits %one, %next : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %fused = jasp.fuse %left, %right : !jasp.QubitArray, !jasp.QubitArray -> !jasp.QubitArray
    func.return %last : !jasp.QuantumState
  }
}
