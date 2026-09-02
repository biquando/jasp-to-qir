builtin.module @jasp_module {
  func.func public @main(%state: !jasp.QuantumState) -> !jasp.QuantumState {
    %one = arith.constant dense<1> : tensor<i64>
    %a0, %s0 = jasp.create_qubits %one, %state : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %a1, %s1 = jasp.create_qubits %one, %s0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %a2, %s2 = jasp.create_qubits %one, %s1 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %a3, %s3 = jasp.create_qubits %one, %s2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %zero = arith.constant dense<0> : tensor<i64>
    %q0 = jasp.get_qubit %a0, %zero : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %q2 = jasp.get_qubit %a2, %zero : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %pair = jasp.fuse %q0, %a1 : !jasp.Qubit, !jasp.QubitArray -> !jasp.QubitArray
    %triple = jasp.fuse %pair, %q2 : !jasp.QubitArray, !jasp.Qubit -> !jasp.QubitArray
    %fused = jasp.fuse %triple, %a3 : !jasp.QubitArray, !jasp.QubitArray -> !jasp.QubitArray
    %last = jasp.delete_qubits %fused, %s3 : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
    func.return %last : !jasp.QuantumState
  }
}
