builtin.module @jasp_module {
  func.func private @measure_helper(%qubit: !jasp.Qubit, %state: !jasp.QuantumState) -> (tensor<i1>, !jasp.QuantumState) {
    %result, %next = jasp.measure %qubit, %state : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    func.return %result, %next : tensor<i1>, !jasp.QuantumState
  }

  func.func public @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %one = arith.constant dense<1> : tensor<i64>
    %zero = arith.constant dense<0> : tensor<i64>
    %qubits, %next = jasp.create_qubits %one, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %qubit = jasp.get_qubit %qubits, %zero : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %result, %last = func.call @measure_helper(%qubit, %next) : (!jasp.Qubit, !jasp.QuantumState) -> (tensor<i1>, !jasp.QuantumState)
    func.return %last : !jasp.QuantumState
  }
}
