builtin.module @jasp_module {
  func.func public @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %two = arith.constant dense<2> : tensor<i64>
    %qubits, %next = jasp.create_qubits %two, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %zero = arith.constant dense<0> : tensor<i64>
    %one = arith.constant dense<1> : tensor<i64>
    %slice = jasp.slice %qubits, %zero, %one : !jasp.QubitArray, tensor<i64>, tensor<i64> -> !jasp.QubitArray
    func.return %next : !jasp.QuantumState
  }
}
