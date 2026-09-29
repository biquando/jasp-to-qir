builtin.module @jasp_module {
  func.func public @main(%arg2: !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QuantumState) {
    %0 = arith.constant dense<3> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<1> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "x" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = arith.constant dense<2> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = jasp.quantum_gate "h" (%7) , %5 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %9 = arith.constant dense<0> : tensor<i64>
    %10 = jasp.get_qubit %1, %9 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %11 = arith.constant dense<3.700000e-01> : tensor<f64>
    %12 = arith.constant dense<-6.100000e-01> : tensor<f64>
    %13 = arith.constant dense<8.300000e-01> : tensor<f64>
    %14 = jasp.quantum_gate "u3" (%10, %11, %12, %13) , %8 : (!jasp.Qubit, tensor<f64>, tensor<f64>, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %15 = arith.constant dense<-2.900000e-01> : tensor<f64>
    %16 = arith.constant dense<4.700000e-01> : tensor<f64>
    %17 = arith.constant dense<-7.100000e-01> : tensor<f64>
    %18 = jasp.quantum_gate "u3" (%4, %15, %16, %17) , %14 : (!jasp.Qubit, tensor<f64>, tensor<f64>, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %19 = arith.constant dense<5.300000e-01> : tensor<f64>
    %20 = arith.constant dense<-1.900000e-01> : tensor<f64>
    %21 = arith.constant dense<9.700000e-01> : tensor<f64>
    %22 = jasp.quantum_gate "u3" (%7, %19, %20, %21) , %18 : (!jasp.Qubit, tensor<f64>, tensor<f64>, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %23 = jasp.quantum_gate "cx" (%7, %10) , %22 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %24 = func.call @tracerizer() : () -> tensor<i64>
    %25 = arith.constant 1 : i64
    %26 = tensor.extract %24[] : tensor<i64>
    %27 = arith.subi %26, %25 : i64
    %28 = tensor.from_elements %27 : tensor<i64>
    %29 = arith.subi %27, %27 : i64
    %30 = tensor.from_elements %29 : tensor<i64>
    %31, %32, %33, %34 = scf.while (%arg21 = %1, %arg22 = %28, %arg23 = %30, %arg24 = %23) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %35 = tensor.extract %arg23[] : tensor<i64>
      %36 = tensor.extract %arg22[] : tensor<i64>
      %37 = arith.cmpi sle, %35, %36 : i64
      scf.condition(%37) %arg21, %arg22, %arg23, %arg24 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg3: !jasp.QubitArray, %arg4: tensor<i64>, %arg5: tensor<i64>, %arg6: !jasp.QuantumState):
      %38 = tensor.extract %arg5[] : tensor<i64>
      %39 = arith.sitofp %38 : i64 to f64
      %40 = arith.constant 1.300000e-01 : f64
      %41 = arith.mulf %40, %39 : f64
      %42 = tensor.from_elements %41 : tensor<f64>
      %43 = tensor.extract %arg5[] : tensor<i64>
      %44 = arith.sitofp %43 : i64 to f64
      %45 = arith.constant -2.300000e-01 : f64
      %46 = arith.mulf %45, %44 : f64
      %47 = tensor.from_elements %46 : tensor<f64>
      %48 = tensor.extract %arg5[] : tensor<i64>
      %49 = arith.sitofp %48 : i64 to f64
      %50 = arith.constant 3.100000e-01 : f64
      %51 = arith.mulf %50, %49 : f64
      %52 = tensor.from_elements %51 : tensor<f64>
      %53 = arith.constant dense<0> : tensor<i64>
      %54 = jasp.get_qubit %arg3, %53 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %55 = jasp.quantum_gate "u3" (%54, %42, %47, %52) , %arg6 : (!jasp.Qubit, tensor<f64>, tensor<f64>, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %56 = arith.constant 1 : i64
      %57 = tensor.extract %arg5[] : tensor<i64>
      %58 = arith.addi %57, %56 : i64
      %59 = tensor.from_elements %58 : tensor<i64>
      %60 = func.call @_jrange_marker(%59, %arg4) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg3, %arg4, %60, %55 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    func.return %1, %34 : !jasp.QubitArray, !jasp.QuantumState
  }
  func.func private @tracerizer() -> (tensor<i64>) {
    %0 = arith.constant dense<3> : tensor<i64>
    func.return %0 : tensor<i64>
  }
  func.func private @_jrange_marker(%arg0: tensor<i64>, %arg1: tensor<i64>) -> (tensor<i64>) {
    func.return %arg0 : tensor<i64>
  }
}
