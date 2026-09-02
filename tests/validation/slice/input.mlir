builtin.module @jasp_module {
  func.func private @slice_start() -> tensor<i64> {
    %value = arith.constant dense<-1> : tensor<i64>
    func.return %value : tensor<i64>
  }

  func.func private @slice_end() -> tensor<i64> {
    %value = arith.constant dense<2> : tensor<i64>
    func.return %value : tensor<i64>
  }

  func.func public @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %two = arith.constant dense<2> : tensor<i64>
    %qubits, %next = jasp.create_qubits %two, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %start = func.call @slice_start() : () -> tensor<i64>
    %end = func.call @slice_end() : () -> tensor<i64>
    %slice = jasp.slice %qubits, %start, %end : !jasp.QubitArray, tensor<i64>, tensor<i64> -> !jasp.QubitArray
    %last = jasp.delete_qubits %slice, %next : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
    func.return %last : !jasp.QuantumState
  }
}
