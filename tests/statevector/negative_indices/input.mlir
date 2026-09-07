builtin.module @jasp_module {
  func.func public @main(%arg2: !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QuantumState) {
    %0 = arith.constant dense<5> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg2 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<-1> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = arith.constant dense<-5> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = arith.constant dense<3.700000e-01> : tensor<f64>
    %9 = jasp.quantum_gate "ry" (%7, %8) , %5 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
    %10 = arith.constant dense<1> : tensor<i64>
    %11 = arith.constant dense<4> : tensor<i64>
    %12 = jasp.slice %1, %10, %11 : !jasp.QubitArray, tensor<i64>, tensor<i64> -> !jasp.QubitArray
    %13 = jasp.get_qubit %12, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %14 = jasp.quantum_gate "cx" (%4, %13) , %9 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %15 = func.call @tracerizer() : () -> tensor<i64>
    %16 = arith.constant 1 : i64
    %17 = tensor.extract %15[] : tensor<i64>
    %18 = arith.subi %17, %16 : i64
    %19 = tensor.from_elements %18 : tensor<i64>
    %20 = arith.subi %18, %18 : i64
    %21 = tensor.from_elements %20 : tensor<i64>
    %22, %23, %24, %25, %26 = scf.while (%arg24 = %12, %arg25 = %1, %arg26 = %19, %arg27 = %21, %arg28 = %14) : (!jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %27 = tensor.extract %arg27[] : tensor<i64>
      %28 = tensor.extract %arg26[] : tensor<i64>
      %29 = arith.cmpi sle, %27, %28 : i64
      scf.condition(%29) %arg24, %arg25, %arg26, %arg27, %arg28 : !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg3: !jasp.QubitArray, %arg4: !jasp.QubitArray, %arg5: tensor<i64>, %arg6: tensor<i64>, %arg7: !jasp.QuantumState):
      %30 = arith.constant 1 : i64
      %31 = tensor.extract %arg6[] : tensor<i64>
      %32 = arith.addi %31, %30 : i64
      %33 = arith.sitofp %32 : i64 to f64
      %34 = arith.constant 2.100000e-01 : f64
      %35 = arith.mulf %34, %33 : f64
      %36 = tensor.from_elements %35 : tensor<f64>
      %37 = arith.constant 3 : i64
      %38 = tensor.extract %arg6[] : tensor<i64>
      %39 = arith.subi %38, %37 : i64
      %40 = tensor.from_elements %39 : tensor<i64>
      %41 = jasp.get_qubit %arg3, %40 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %42 = jasp.quantum_gate "ry" (%41, %36) , %arg7 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %43 = arith.constant 1 : i64
      %44 = tensor.extract %arg6[] : tensor<i64>
      %45 = arith.addi %44, %43 : i64
      %46 = arith.sitofp %45 : i64 to f64
      %47 = arith.constant 1.700000e-01 : f64
      %48 = arith.mulf %47, %46 : f64
      %49 = tensor.from_elements %48 : tensor<f64>
      %50 = jasp.get_qubit %arg4, %arg6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %51 = jasp.quantum_gate "rz" (%50, %49) , %42 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
      %52 = arith.constant 1 : i64
      %53 = tensor.extract %arg6[] : tensor<i64>
      %54 = arith.addi %53, %52 : i64
      %55 = tensor.from_elements %54 : tensor<i64>
      %56 = func.call @_jrange_marker(%55, %arg5) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg3, %arg4, %arg5, %56, %51 : !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    func.return %1, %26 : !jasp.QubitArray, !jasp.QuantumState
  }
  func.func private @tracerizer() -> (tensor<i64>) {
    %0 = arith.constant dense<3> : tensor<i64>
    func.return %0 : tensor<i64>
  }
  func.func private @_jrange_marker(%arg0: tensor<i64>, %arg1: tensor<i64>) -> (tensor<i64>) {
    func.return %arg0 : tensor<i64>
  }
}
