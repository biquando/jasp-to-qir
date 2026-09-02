builtin.module @jasp_module {
  func.func public @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %bit = arith.constant dense<true> : tensor<i1>
    %parity = jasp.parity %bit {expectation = 0 : i64, observable = 0 : i64} : tensor<i1> -> tensor<i1>
    func.return %state : !jasp.QuantumState
  }
}
