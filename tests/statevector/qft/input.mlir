builtin.module @jasp_module {
  func.func public @main(%arg143: !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QuantumState) {
    %0 = arith.constant dense<5> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg143 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<1> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = arith.constant dense<2> : tensor<i64>
    %7 = jasp.get_qubit %1, %6 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %8 = jasp.quantum_gate "cx" (%4, %7) , %5 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %9 = arith.constant dense<3> : tensor<i64>
    %10 = jasp.get_qubit %1, %9 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %11 = jasp.quantum_gate "x" (%10) , %8 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %12 = arith.constant dense<4> : tensor<i64>
    %13 = jasp.get_qubit %1, %12 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %14 = jasp.quantum_gate "x" (%13) , %11 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %15 = func.call @jasp_qft(%1, %14) : (!jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
    func.return %1, %15 : !jasp.QubitArray, !jasp.QuantumState
  }
  func.func private @jasp_qft(%arg33: !jasp.QubitArray, %arg34: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.get_size %arg33 : !jasp.QubitArray -> tensor<i64>
    %1 = arith.constant 1 : i64
    %2 = tensor.extract %0[] : tensor<i64>
    %3 = arith.subi %2, %1 : i64
    %4 = tensor.from_elements %3 : tensor<i64>
    %5 = arith.subi %3, %3 : i64
    %6 = tensor.from_elements %5 : tensor<i64>
    %7, %8, %9, %10, %11 = scf.while (%arg130 = %0, %arg131 = %arg33, %arg132 = %4, %arg133 = %6, %arg134 = %arg34) : (tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %12 = tensor.extract %arg133[] : tensor<i64>
      %13 = tensor.extract %arg132[] : tensor<i64>
      %14 = arith.cmpi sle, %12, %13 : i64
      scf.condition(%14) %arg130, %arg131, %arg132, %arg133, %arg134 : tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg60: tensor<i64>, %arg61: !jasp.QubitArray, %arg62: tensor<i64>, %arg63: tensor<i64>, %arg64: !jasp.QuantumState):
      %15 = arith.constant 1 : i64
      %16 = tensor.extract %arg60[] : tensor<i64>
      %17 = arith.subi %16, %15 : i64
      %18 = tensor.extract %arg63[] : tensor<i64>
      %19 = arith.subi %17, %18 : i64
      %20 = tensor.from_elements %19 : tensor<i64>
      %21 = jasp.get_qubit %arg61, %20 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %22 = jasp.quantum_gate "h" (%21) , %arg64 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %23 = tensor.extract %arg60[] : tensor<i64>
      %24 = tensor.extract %arg63[] : tensor<i64>
      %25 = arith.subi %23, %24 : i64
      %26 = arith.constant 1 : i64
      %27 = arith.subi %25, %26 : i64
      %28 = arith.constant 1 : i64
      %29 = arith.subi %27, %28 : i64
      %30 = tensor.from_elements %29 : tensor<i64>
      %31 = arith.subi %29, %29 : i64
      %32 = tensor.from_elements %31 : tensor<i64>
      %33, %34, %35, %36, %37, %38 = scf.while (%arg106 = %arg60, %arg107 = %arg63, %arg108 = %arg61, %arg109 = %30, %arg110 = %32, %arg111 = %22) : (tensor<i64>, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (tensor<i64>, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
        %39 = tensor.extract %arg110[] : tensor<i64>
        %40 = tensor.extract %arg109[] : tensor<i64>
        %41 = arith.cmpi sle, %39, %40 : i64
        scf.condition(%41) %arg106, %arg107, %arg108, %arg109, %arg110, %arg111 : tensor<i64>, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
      } do {
      ^bb1(%arg67: tensor<i64>, %arg68: tensor<i64>, %arg69: !jasp.QubitArray, %arg70: tensor<i64>, %arg71: tensor<i64>, %arg72: !jasp.QuantumState):
        %42 = arith.constant 2 : i64
        %43 = tensor.extract %arg71[] : tensor<i64>
        %44 = arith.addi %43, %42 : i64
        %45 = arith.sitofp %44 : i64 to f64
        %46 = arith.constant 2.000000e+00 : f64
        %47 = math.powf %46, %45 : f64
        %48 = arith.constant 6.2831853071795862 : f64
        %49 = arith.divf %48, %47 : f64
        %50 = arith.constant 1 : i64
        %51 = tensor.extract %arg67[] : tensor<i64>
        %52 = arith.subi %51, %50 : i64
        %53 = tensor.extract %arg71[] : tensor<i64>
        %54 = tensor.extract %arg68[] : tensor<i64>
        %55 = arith.addi %53, %54 : i64
        %56 = arith.constant 1 : i64
        %57 = arith.addi %55, %56 : i64
        %58 = arith.subi %52, %57 : i64
        %59 = tensor.from_elements %58 : tensor<i64>
        %60 = jasp.get_qubit %arg69, %59 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %61 = arith.constant 1 : i64
        %62 = tensor.extract %arg67[] : tensor<i64>
        %63 = arith.subi %62, %61 : i64
        %64 = tensor.extract %arg68[] : tensor<i64>
        %65 = arith.subi %63, %64 : i64
        %66 = tensor.from_elements %65 : tensor<i64>
        %67 = jasp.get_qubit %arg69, %66 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %68 = arith.constant 5.000000e-01 : f64
        %69 = arith.mulf %68, %49 : f64
        %70 = tensor.from_elements %69 : tensor<f64>
        %71 = jasp.quantum_gate "p" (%67, %70) , %arg72 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
        %72 = arith.constant 5.000000e-01 : f64
        %73 = arith.mulf %72, %49 : f64
        %74 = tensor.from_elements %73 : tensor<f64>
        %75 = jasp.quantum_gate "p" (%60, %74) , %71 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
        %76 = jasp.quantum_gate "cx" (%60, %67) , %75 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %77 = arith.constant -5.000000e-01 : f64
        %78 = arith.mulf %77, %49 : f64
        %79 = tensor.from_elements %78 : tensor<f64>
        %80 = jasp.quantum_gate "p" (%67, %79) , %76 : (!jasp.Qubit, tensor<f64>) , !jasp.QuantumState -> !jasp.QuantumState
        %81 = jasp.quantum_gate "cx" (%60, %67) , %80 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %82 = arith.constant 1 : i64
        %83 = tensor.extract %arg71[] : tensor<i64>
        %84 = arith.addi %83, %82 : i64
        %85 = tensor.from_elements %84 : tensor<i64>
        %86 = func.call @_jrange_marker(%85, %arg70) : (tensor<i64>, tensor<i64>) -> tensor<i64>
        scf.yield %arg67, %arg68, %arg69, %arg70, %86, %81 : tensor<i64>, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
      }
      %87 = arith.constant 1 : i64
      %88 = tensor.extract %arg63[] : tensor<i64>
      %89 = arith.addi %88, %87 : i64
      %90 = tensor.from_elements %89 : tensor<i64>
      %91 = func.call @_jrange_marker(%90, %arg62) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg60, %arg61, %arg62, %91, %38 : tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %92 = arith.constant dense<2> : tensor<i64>
    %93 = func.call @floor_divide(%0, %92) : (tensor<i64>, tensor<i64>) -> tensor<i64>
    %94 = arith.constant 1 : i64
    %95 = tensor.extract %93[] : tensor<i64>
    %96 = arith.subi %95, %94 : i64
    %97 = tensor.from_elements %96 : tensor<i64>
    %98 = arith.subi %96, %96 : i64
    %99 = tensor.from_elements %98 : tensor<i64>
    %100, %101, %102, %103, %104 = scf.while (%arg47 = %arg33, %arg48 = %0, %arg49 = %97, %arg50 = %99, %arg51 = %11) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %105 = tensor.extract %arg50[] : tensor<i64>
      %106 = tensor.extract %arg49[] : tensor<i64>
      %107 = arith.cmpi sle, %105, %106 : i64
      scf.condition(%107) %arg47, %arg48, %arg49, %arg50, %arg51 : !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb2(%arg35: !jasp.QubitArray, %arg36: tensor<i64>, %arg37: tensor<i64>, %arg38: tensor<i64>, %arg39: !jasp.QuantumState):
      %108 = jasp.get_qubit %arg35, %arg38 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %109 = tensor.extract %arg36[] : tensor<i64>
      %110 = tensor.extract %arg38[] : tensor<i64>
      %111 = arith.subi %109, %110 : i64
      %112 = arith.constant 1 : i64
      %113 = arith.subi %111, %112 : i64
      %114 = tensor.from_elements %113 : tensor<i64>
      %115 = jasp.get_qubit %arg35, %114 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %116 = jasp.quantum_gate "cx" (%108, %115) , %arg39 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %117 = jasp.quantum_gate "cx" (%115, %108) , %116 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %118 = jasp.quantum_gate "cx" (%108, %115) , %117 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %119 = arith.constant 1 : i64
      %120 = tensor.extract %arg38[] : tensor<i64>
      %121 = arith.addi %120, %119 : i64
      %122 = tensor.from_elements %121 : tensor<i64>
      %123 = func.call @_jrange_marker(%122, %arg37) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg35, %arg36, %arg37, %123, %118 : !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    func.return %104 : !jasp.QuantumState
  }
  func.func private @_jrange_marker(%arg31: tensor<i64>, %arg32: tensor<i64>) -> (tensor<i64>) {
    func.return %arg31 : tensor<i64>
  }
  func.func private @floor_divide(%arg7: tensor<i64>, %arg8: tensor<i64>) -> (tensor<i64>) {
    %0 = tensor.extract %arg8[] : tensor<i64>
    %1 = tensor.extract %arg7[] : tensor<i64>
    %2 = arith.constant -1 : i64
    %3 = arith.constant -9223372036854775808 : i64
    %4 = arith.constant 0 : i64
    %5 = arith.constant 1 : i64
    %6 = arith.cmpi eq, %0, %4 : i64
    %7 = arith.constant -9223372036854775808 : i64
    %8 = arith.cmpi eq, %1, %7 : i64
    %9 = arith.constant -1 : i64
    %10 = arith.cmpi eq, %0, %9 : i64
    %11 = arith.andi %8, %10 : i1
    %12 = arith.ori %6, %11 : i1
    %13 = arith.select %12, %5, %0 : i64
    %14 = arith.divsi %1, %13 : i64
    %15 = arith.select %11, %3, %14 : i64
    %16 = arith.select %6, %2, %15 : i64
    %17 = tensor.from_elements %16 : tensor<i64>
    %18 = tensor.extract %arg7[] : tensor<i64>
    %19 = arith.constant 0 : i64
    %20 = arith.constant 63 : i64
    %21 = arith.constant 1 : i64
    %22 = arith.cmpi eq, %18, %19 : i64
    %23 = arith.shrsi %18, %20 : i64
    %24 = arith.ori %23, %21 : i64
    %25 = arith.select %22, %19, %24 : i64
    %26 = arith.constant 0 : i64
    %27 = arith.constant 63 : i64
    %28 = arith.constant 1 : i64
    %29 = arith.cmpi eq, %0, %26 : i64
    %30 = arith.shrsi %0, %27 : i64
    %31 = arith.ori %30, %28 : i64
    %32 = arith.select %29, %26, %31 : i64
    %33 = arith.cmpi ne, %25, %32 : i64
    %34 = tensor.extract %arg7[] : tensor<i64>
    %35 = arith.constant 0 : i64
    %36 = arith.constant 0 : i64
    %37 = arith.constant 1 : i64
    %38 = arith.cmpi eq, %0, %36 : i64
    %39 = arith.constant -9223372036854775808 : i64
    %40 = arith.cmpi eq, %34, %39 : i64
    %41 = arith.constant -1 : i64
    %42 = arith.cmpi eq, %0, %41 : i64
    %43 = arith.andi %40, %42 : i1
    %44 = arith.ori %38, %43 : i1
    %45 = arith.select %44, %37, %0 : i64
    %46 = arith.remsi %34, %45 : i64
    %47 = arith.select %43, %35, %46 : i64
    %48 = arith.select %38, %34, %47 : i64
    %49 = arith.constant 0 : i64
    %50 = arith.cmpi ne, %48, %49 : i64
    %51 = arith.andi %33, %50 : i1
    %52 = tensor.from_elements %51 : tensor<i1>
    %53 = arith.constant 1 : i64
    %54 = arith.subi %16, %53 : i64
    %55 = tensor.from_elements %54 : tensor<i64>
    %56 = func.call @_where(%52, %55, %17) : (tensor<i1>, tensor<i64>, tensor<i64>) -> tensor<i64>
    func.return %56 : tensor<i64>
  }
  func.func private @_where(%arg0: tensor<i1>, %arg1: tensor<i64>, %arg2: tensor<i64>) -> (tensor<i64>) {
    %0 = tensor.extract %arg0[] : tensor<i1>
    %1 = tensor.extract %arg1[] : tensor<i64>
    %2 = tensor.extract %arg2[] : tensor<i64>
    %3 = arith.select %0, %1, %2 : i64
    %4 = tensor.from_elements %3 : tensor<i64>
    func.return %4 : tensor<i64>
  }
}
