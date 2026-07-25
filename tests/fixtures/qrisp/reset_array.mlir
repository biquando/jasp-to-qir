builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<2> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = jasp.reset %1, %2 : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
    %4, %5 = jasp.measure %1, %3 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %4, %5 : tensor<i64>, !jasp.QuantumState
  }
}
