builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i1>, tensor<i1>, tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<2> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3, %4 = jasp.create_qubits %0, %2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %5 = arith.constant dense<0> : tensor<i64>
    %6 = jasp.get_qubit %3, %5 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %7 = jasp.quantum_gate "x" (%6) , %4 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %8, %9 = jasp.measure %6, %7 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %10 = arith.constant dense<1> : tensor<i64>
    %11 = jasp.get_qubit %3, %10 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %12, %13 = jasp.measure %11, %9 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %14 = tensor.extract %8[] : tensor<i1>
    %15 = arith.constant true
    %16 = arith.xori %14, %15 : i1
    %17 = scf.if %16 -> (!jasp.QuantumState) {
      %18 = arith.constant dense<0> : tensor<i64>
      %19 = jasp.get_qubit %1, %18 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %20 = jasp.quantum_gate "z" (%19) , %13 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %20 : !jasp.QuantumState
    } else {
      %21 = arith.constant dense<0> : tensor<i64>
      %22 = jasp.get_qubit %1, %21 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %23 = jasp.quantum_gate "x" (%22) , %13 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %23 : !jasp.QuantumState
    }
    %24 = tensor.extract %12[] : tensor<i1>
    %25 = arith.constant true
    %26 = arith.xori %24, %25 : i1
    %27 = scf.if %26 -> (!jasp.QuantumState) {
      %28 = arith.constant dense<1> : tensor<i64>
      %29 = jasp.get_qubit %1, %28 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %30 = jasp.quantum_gate "x" (%29) , %17 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %30 : !jasp.QuantumState
    } else {
      %31 = arith.constant dense<1> : tensor<i64>
      %32 = jasp.get_qubit %1, %31 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %33 = jasp.quantum_gate "z" (%32) , %17 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %33 : !jasp.QuantumState
    }
    %34, %35 = jasp.measure %1, %27 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %8, %12, %34, %35 : tensor<i1>, tensor<i1>, tensor<i64>, !jasp.QuantumState
  }
}
