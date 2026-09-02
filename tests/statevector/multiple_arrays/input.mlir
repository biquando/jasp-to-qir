builtin.module @jasp_module {
  func.func public @main(%arg2: !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QubitArray, !jasp.QubitArray, !jasp.QuantumState) {
    %0 = arith.constant dense<3> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<2> : tensor<i64>
    %4, %5 = jasp.create_qubits %3, %2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %6 = arith.constant dense<1> : tensor<i64>
    %7, %8 = jasp.create_qubits %6, %5 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %9 = arith.constant dense<0> : tensor<i64>
    %10 = jasp.get_qubit %1, %9 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %11 = jasp.quantum_gate "h" (%10) , %8 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %12 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %13 = arith.constant dense<3.750000e-01> : tensor<f64>
    %14 = jasp.quantum_gate "rx" (%12, %13) , %11 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %15 = func.call @tracerizer() : () -> tensor<i64>
    %16 = arith.constant 1 : i64
    %17 = tensor.extract %15[] : tensor<i64>
    %18 = arith.subi %17, %16 : i64
    %19 = tensor.from_elements %18 : tensor<i64>
    %20 = arith.subi %18, %18 : i64
    %21 = tensor.from_elements %20 : tensor<i64>
    %22, %23, %24, %25, %26 = scf.while (%arg10 = %1, %arg11 = %4, %arg12 = %19, %arg13 = %21, %arg14 = %14) : (!jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %27 = tensor.extract %arg13[] : tensor<i64>
      %28 = tensor.extract %arg12[] : tensor<i64>
      %29 = arith.cmpi sle, %27, %28 : i64
      scf.condition(%29) %arg10, %arg11, %arg12, %arg13, %arg14 : !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg3: !jasp.QubitArray, %arg4: !jasp.QubitArray, %arg5: tensor<i64>, %arg6: tensor<i64>, %arg7: !jasp.QuantumState):
      %30 = jasp.get_qubit %arg3, %arg6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %31 = jasp.get_qubit %arg4, %arg6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %32 = jasp.quantum_gate "cx" (%30, %31) , %arg7 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %33 = arith.constant dense<2.500000e-01> : tensor<f64>
      %34 = jasp.quantum_gate "ry" (%31, %33) , %32 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %35 = arith.constant 1 : i64
      %36 = tensor.extract %arg6[] : tensor<i64>
      %37 = arith.addi %36, %35 : i64
      %38 = tensor.from_elements %37 : tensor<i64>
      %39 = func.call @_jrange_marker(%38, %arg5) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg3, %arg4, %arg5, %39, %34 : !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %40 = jasp.get_qubit %4, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %41 = jasp.get_qubit %7, %9 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %42 = jasp.quantum_gate "cz" (%40, %41) , %26 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    func.return %1, %4, %7, %42 : !jasp.QubitArray, !jasp.QubitArray, !jasp.QubitArray, !jasp.QuantumState
  }
  func.func private @tracerizer() -> (tensor<i64>) {
    %0 = arith.constant dense<2> : tensor<i64>
    func.return %0 : tensor<i64>
  }
  func.func private @_jrange_marker(%arg0: tensor<i64>, %arg1: tensor<i64>) -> (tensor<i64>) {
    func.return %arg0 : tensor<i64>
  }
}
