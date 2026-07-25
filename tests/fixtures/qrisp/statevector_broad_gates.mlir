builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QuantumState) {
    %0 = arith.constant dense<4> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = arith.constant dense<1> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = jasp.quantum_gate "h" (%7) , %5 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %9 = arith.constant dense<2> : tensor<i64>
    %10 = jasp.get_qubit %1, %9 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %11 = jasp.quantum_gate "x" (%10) , %8 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %12 = arith.constant dense<3> : tensor<i64>
    %13 = jasp.get_qubit %1, %12 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %14 = jasp.quantum_gate "y" (%13) , %11 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %15 = jasp.quantum_gate "z" (%4) , %14 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %16 = jasp.quantum_gate "s" (%4) , %15 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %17 = jasp.quantum_gate "s_dg" (%7) , %16 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %18 = jasp.quantum_gate "t" (%10) , %17 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %19 = jasp.quantum_gate "t_dg" (%13) , %18 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %20 = arith.constant dense<1.250000e-01> : tensor<f64>
    %21 = jasp.quantum_gate "rx" (%4, %20) , %19 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %22 = arith.constant dense<-2.500000e-01> : tensor<f64>
    %23 = jasp.quantum_gate "ry" (%7, %22) , %21 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %24 = arith.constant dense<5.000000e-01> : tensor<f64>
    %25 = jasp.quantum_gate "rz" (%10, %24) , %23 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %26 = jasp.quantum_gate "cx" (%4, %10) , %25 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %27 = jasp.quantum_gate "cz" (%7, %13) , %26 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %28 = jasp.quantum_gate "h" (%13) , %27 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %29 = jasp.quantum_gate "t_dg" (%7) , %28 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %30 = jasp.quantum_gate "t_dg" (%4) , %29 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %31 = jasp.quantum_gate "cx" (%13, %7) , %30 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %32 = jasp.quantum_gate "cx" (%4, %13) , %31 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %33 = jasp.quantum_gate "t" (%7) , %32 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %34 = jasp.quantum_gate "cx" (%4, %7) , %33 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %35 = jasp.quantum_gate "t" (%13) , %34 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %36 = jasp.quantum_gate "cx" (%4, %13) , %35 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %37 = jasp.quantum_gate "t_dg" (%7) , %36 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %38 = jasp.quantum_gate "cx" (%13, %7) , %37 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %39 = jasp.quantum_gate "t" (%7) , %38 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %40 = jasp.quantum_gate "t_dg" (%13) , %39 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %41 = jasp.quantum_gate "cx" (%4, %7) , %40 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %42 = jasp.quantum_gate "h" (%13) , %41 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    func.return %1, %42 : !jasp.QubitArray, !jasp.QuantumState
  }
}
