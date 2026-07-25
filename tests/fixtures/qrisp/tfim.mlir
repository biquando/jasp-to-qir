builtin.module @jasp_module {
  func.func public @main(%arg2: !jasp.QuantumState) -> (tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<5> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = func.call @tracerizer() : () -> tensor<i64>
    %4 = arith.constant 1 : i64
    %5 = tensor.extract %3[] : tensor<i64>
    %6 = arith.subi %5, %4 : i64
    %7 = tensor.from_elements %6 : tensor<i64>
    %8 = arith.subi %6, %6 : i64
    %9 = tensor.from_elements %8 : tensor<i64>
    %10, %11, %12, %13 = scf.while (%arg9 = %1, %arg10 = %7, %arg11 = %9, %arg12 = %2) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %14 = tensor.extract %arg11[] : tensor<i64>
      %15 = tensor.extract %arg10[] : tensor<i64>
      %16 = arith.cmpi sle, %14, %15 : i64
      scf.condition(%16) %arg9, %arg10, %arg11, %arg12 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg3: !jasp.QubitArray, %arg4: tensor<i64>, %arg5: tensor<i64>, %arg6: !jasp.QuantumState):
      %17 = arith.constant dense<0> : tensor<i64>
      %18 = jasp.get_qubit %arg3, %17 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %19 = arith.constant dense<1> : tensor<i64>
      %20 = jasp.get_qubit %arg3, %19 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %21 = jasp.quantum_gate "cx" (%18, %20) , %arg6 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %22 = arith.constant dense<5.000000e-01> : tensor<f64>
      %23 = jasp.quantum_gate "rz" (%20, %22) , %21 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %24 = jasp.quantum_gate "cx" (%18, %20) , %23 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %25 = arith.constant dense<2> : tensor<i64>
      %26 = jasp.get_qubit %arg3, %25 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %27 = jasp.quantum_gate "cx" (%20, %26) , %24 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %28 = jasp.quantum_gate "rz" (%26, %22) , %27 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %29 = jasp.quantum_gate "cx" (%20, %26) , %28 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %30 = arith.constant dense<3> : tensor<i64>
      %31 = jasp.get_qubit %arg3, %30 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %32 = jasp.quantum_gate "cx" (%26, %31) , %29 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %33 = jasp.quantum_gate "rz" (%31, %22) , %32 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %34 = jasp.quantum_gate "cx" (%26, %31) , %33 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %35 = arith.constant dense<4> : tensor<i64>
      %36 = jasp.get_qubit %arg3, %35 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %37 = jasp.quantum_gate "cx" (%31, %36) , %34 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %38 = jasp.quantum_gate "rz" (%36, %22) , %37 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %39 = jasp.quantum_gate "cx" (%31, %36) , %38 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %40 = arith.constant dense<2.500000e-01> : tensor<f64>
      %41 = jasp.quantum_gate "rx" (%18, %40) , %39 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %42 = jasp.quantum_gate "rx" (%20, %40) , %41 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %43 = jasp.quantum_gate "rx" (%26, %40) , %42 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %44 = jasp.quantum_gate "rx" (%31, %40) , %43 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %45 = jasp.quantum_gate "rx" (%36, %40) , %44 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %46 = arith.constant 1 : i64
      %47 = tensor.extract %arg5[] : tensor<i64>
      %48 = arith.addi %47, %46 : i64
      %49 = tensor.from_elements %48 : tensor<i64>
      %50 = func.call @_jrange_marker(%49, %arg4) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg3, %arg4, %50, %45 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %51, %52 = jasp.measure %1, %13 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %51, %52 : tensor<i64>, !jasp.QuantumState
  }
  func.func private @tracerizer() -> (tensor<i64>) {
    %0 = arith.constant dense<4> : tensor<i64>
    func.return %0 : tensor<i64>
  }
  func.func private @_jrange_marker(%arg0: tensor<i64>, %arg1: tensor<i64>) -> (tensor<i64>) {
    func.return %arg0 : tensor<i64>
  }
}
