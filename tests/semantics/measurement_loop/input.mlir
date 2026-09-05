builtin.module @jasp_module {
  func.func public @main(%arg0: !jasp.QuantumState) -> (tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<1> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg0 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "x" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6, %7, %8, %9 = scf.while (%arg25 = %1, %arg26 = %3, %arg27 = %3, %arg28 = %5) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %10 = arith.constant 3 : i64
      %11 = tensor.extract %arg26[] : tensor<i64>
      %12 = arith.cmpi slt, %11, %10 : i64
      scf.condition(%12) %arg25, %arg26, %arg27, %arg28 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg11: !jasp.QubitArray, %arg12: tensor<i64>, %arg13: tensor<i64>, %arg14: !jasp.QuantumState):
      %13 = arith.constant dense<0> : tensor<i64>
      %14 = jasp.get_qubit %arg11, %13 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %15, %16 = jasp.measure %14, %arg14 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
      %17 = jasp.quantum_gate "x" (%14) , %16 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %18 = arith.constant 1 : i64
      %19 = tensor.extract %arg12[] : tensor<i64>
      %20 = arith.addi %19, %18 : i64
      %21 = tensor.from_elements %20 : tensor<i64>
      %22 = tensor.extract %15[] : tensor<i1>
      %23 = arith.extui %22 : i1 to i64
      %24 = tensor.extract %arg12[] : tensor<i64>
      %25 = arith.constant 0 : i64
      %26 = arith.shli %23, %24 : i64
      %27 = arith.constant 64 : i64
      %28 = arith.cmpi ugt, %27, %24 : i64
      %29 = arith.select %28, %26, %25 : i64
      %30 = tensor.extract %arg13[] : tensor<i64>
      %31 = arith.ori %30, %29 : i64
      %32 = tensor.from_elements %31 : tensor<i64>
      scf.yield %arg11, %21, %32, %17 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %33 = arith.constant 1 : i64
    %34 = tensor.extract %8[] : tensor<i64>
    %35 = arith.andi %34, %33 : i64
    %36 = tensor.from_elements %35 : tensor<i64>
    %37 = arith.constant 1 : i64
    %38 = tensor.extract %8[] : tensor<i64>
    %39 = arith.constant 63 : i64
    %40 = arith.shrsi %38, %39 : i64
    %41 = arith.shrsi %38, %37 : i64
    %42 = arith.constant 64 : i64
    %43 = arith.cmpi ugt, %42, %37 : i64
    %44 = arith.select %43, %41, %40 : i64
    %45 = arith.constant 1 : i64
    %46 = arith.andi %44, %45 : i64
    %47 = tensor.from_elements %46 : tensor<i64>
    %48 = arith.constant 2 : i64
    %49 = tensor.extract %8[] : tensor<i64>
    %50 = arith.constant 63 : i64
    %51 = arith.shrsi %49, %50 : i64
    %52 = arith.shrsi %49, %48 : i64
    %53 = arith.constant 64 : i64
    %54 = arith.cmpi ugt, %53, %48 : i64
    %55 = arith.select %54, %52, %51 : i64
    %56 = arith.constant 1 : i64
    %57 = arith.andi %55, %56 : i64
    %58 = tensor.from_elements %57 : tensor<i64>
    func.return %36, %47, %58, %9 : tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState
  }
}
