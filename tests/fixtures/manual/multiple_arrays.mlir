builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i1>, tensor<i1>, tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<3> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<1> : tensor<i64>
    %4, %5 = jasp.create_qubits %3, %2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %6, %7 = jasp.create_qubits %3, %5 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %8 = arith.constant dense<0> : tensor<i64>
    %9 = jasp.get_qubit %1, %8 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %10 = jasp.quantum_gate "h" (%9) , %7 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %11 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %12 = jasp.quantum_gate "cx" (%9, %11) , %10 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %13 = arith.constant dense<2> : tensor<i64>
    %14 = jasp.get_qubit %1, %13 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %15 = jasp.quantum_gate "cx" (%11, %14) , %12 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %16 = jasp.get_qubit %6, %8 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %17 = jasp.quantum_gate "h" (%16) , %15 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %18, %19 = jasp.measure %16, %17 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %20 = tensor.extract %18[] : tensor<i1>
    %21 = arith.constant true
    %22 = arith.xori %20, %21 : i1
    %23 = scf.if %22 -> (!jasp.QuantumState) {
      %24 = arith.constant dense<2> : tensor<i64>
      %25 = jasp.get_qubit %1, %24 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %26 = jasp.quantum_gate "z" (%25) , %19 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %26 : !jasp.QuantumState
    } else {
      %27 = arith.constant dense<1> : tensor<i64>
      %28 = jasp.get_qubit %1, %27 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %29 = jasp.quantum_gate "x" (%28) , %19 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %29 : !jasp.QuantumState
    }
    %30 = jasp.get_qubit %4, %8 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %31 = jasp.quantum_gate "cx" (%9, %30) , %23 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %32 = jasp.quantum_gate "cx" (%11, %30) , %31 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %33, %34 = jasp.measure %30, %32 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %35 = tensor.extract %33[] : tensor<i1>
    %36 = arith.constant true
    %37 = arith.xori %35, %36 : i1
    %38 = scf.if %37 -> (!jasp.QuantumState) {
      scf.yield %34 : !jasp.QuantumState
    } else {
      %39 = arith.constant dense<1> : tensor<i64>
      %40 = jasp.get_qubit %1, %39 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %41 = jasp.quantum_gate "x" (%40) , %34 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %41 : !jasp.QuantumState
    }
    %42, %43 = jasp.measure %1, %38 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %18, %33, %42, %43 : tensor<i1>, tensor<i1>, tensor<i64>, !jasp.QuantumState
  }
}
