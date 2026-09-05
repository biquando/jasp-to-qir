builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i1>, tensor<i1>, tensor<i1>, tensor<i1>, !jasp.QuantumState) {
    %0 = arith.constant dense<3> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "x" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = arith.constant dense<2> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = jasp.quantum_gate "x" (%7) , %5 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %9, %10 = jasp.measure %4, %8 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %11 = arith.constant dense<1> : tensor<i64>
    %12 = jasp.get_qubit %1, %11 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %13, %14 = jasp.measure %12, %10 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %15 = tensor.extract %9[] : tensor<i1>
    %16 = arith.constant true
    %17 = arith.xori %15, %16 : i1
    %18, %19 = scf.if %17 -> (tensor<i1>, !jasp.QuantumState) {
      %20 = arith.constant dense<1> : tensor<i64>
      %21 = jasp.get_qubit %1, %20 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %22, %23 = jasp.measure %21, %14 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
      scf.yield %22, %23 : tensor<i1>, !jasp.QuantumState
    } else {
      %24 = arith.constant dense<2> : tensor<i64>
      %25 = jasp.get_qubit %1, %24 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %26, %27 = jasp.measure %25, %14 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
      scf.yield %26, %27 : tensor<i1>, !jasp.QuantumState
    }
    %28 = tensor.extract %13[] : tensor<i1>
    %29 = arith.constant true
    %30 = arith.xori %28, %29 : i1
    %31, %32 = scf.if %30 -> (tensor<i1>, !jasp.QuantumState) {
      %33 = arith.constant dense<1> : tensor<i64>
      %34 = jasp.get_qubit %1, %33 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %35, %36 = jasp.measure %34, %19 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
      scf.yield %35, %36 : tensor<i1>, !jasp.QuantumState
    } else {
      %37 = arith.constant dense<2> : tensor<i64>
      %38 = jasp.get_qubit %1, %37 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %39, %40 = jasp.measure %38, %19 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
      scf.yield %39, %40 : tensor<i1>, !jasp.QuantumState
    }
    func.return %9, %13, %18, %31, %32 : tensor<i1>, tensor<i1>, tensor<i1>, tensor<i1>, !jasp.QuantumState
  }
}
