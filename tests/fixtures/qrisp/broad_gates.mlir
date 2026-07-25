builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<4> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = arith.constant dense<1> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = jasp.quantum_gate "x" (%7) , %5 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %9 = arith.constant dense<2> : tensor<i64>
    %10 = jasp.get_qubit %1, %9 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %11 = jasp.quantum_gate "y" (%10) , %8 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %12 = arith.constant dense<3> : tensor<i64>
    %13 = jasp.get_qubit %1, %12 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %14 = jasp.quantum_gate "z" (%13) , %11 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %15 = jasp.quantum_gate "s" (%4) , %14 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %16 = jasp.quantum_gate "s_dg" (%7) , %15 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %17 = jasp.quantum_gate "t" (%10) , %16 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %18 = jasp.quantum_gate "t_dg" (%13) , %17 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %19 = arith.constant dense<1.250000e-01> : tensor<f64>
    %20 = jasp.quantum_gate "rx" (%4, %19) , %18 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %21 = arith.constant dense<2.500000e-01> : tensor<f64>
    %22 = jasp.quantum_gate "ry" (%7, %21) , %20 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %23 = arith.constant dense<5.000000e-01> : tensor<f64>
    %24 = jasp.quantum_gate "rz" (%10, %23) , %22 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %25 = jasp.quantum_gate "cx" (%4, %7) , %24 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %26 = jasp.quantum_gate "cz" (%7, %10) , %25 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %27 = jasp.quantum_gate "h" (%13) , %26 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %28 = jasp.quantum_gate "t_dg" (%7) , %27 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %29 = jasp.quantum_gate "t_dg" (%4) , %28 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %30 = jasp.quantum_gate "cx" (%13, %7) , %29 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %31 = jasp.quantum_gate "cx" (%4, %13) , %30 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %32 = jasp.quantum_gate "t" (%7) , %31 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %33 = jasp.quantum_gate "cx" (%4, %7) , %32 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %34 = jasp.quantum_gate "t" (%13) , %33 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %35 = jasp.quantum_gate "cx" (%4, %13) , %34 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %36 = jasp.quantum_gate "t_dg" (%7) , %35 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %37 = jasp.quantum_gate "cx" (%13, %7) , %36 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %38 = jasp.quantum_gate "t" (%7) , %37 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %39 = jasp.quantum_gate "t_dg" (%13) , %38 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %40 = jasp.quantum_gate "cx" (%4, %7) , %39 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %41 = jasp.quantum_gate "h" (%13) , %40 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %42 = jasp.reset %13, %41 : !jasp.Qubit, !jasp.QuantumState -> !jasp.QuantumState
    %43, %44 = jasp.measure %1, %42 : !jasp.QubitArray, !jasp.QuantumState -> tensor<i64>, !jasp.QuantumState
    func.return %43, %44 : tensor<i64>, !jasp.QuantumState
  }
}
