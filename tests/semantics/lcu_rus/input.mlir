builtin.module @jasp_module {
  func.func public @main(%arg571: !jasp.QuantumState) -> (tensor<i1>, !jasp.QuantumState) {
    %0, %1, %2 = func.call @lcu_trial(%arg571) : (!jasp.QuantumState) -> (tensor<i1>, !jasp.QubitArray, !jasp.QuantumState)
    %3 = tensor.extract %0[] : tensor<i1>
    %4 = arith.constant true
    %5 = arith.xori %3, %4 : i1
    %6, %7, %8 = scf.if %5 -> (tensor<i1>, !jasp.QubitArray, !jasp.QuantumState) {
      %9, %10, %11 = scf.while (%arg593 = %0, %arg594 = %1, %arg595 = %2) : (tensor<i1>, !jasp.QubitArray, !jasp.QuantumState) -> (tensor<i1>, !jasp.QubitArray, !jasp.QuantumState) {
        %12 = tensor.extract %arg593[] : tensor<i1>
        %13 = arith.constant true
        %14 = arith.xori %12, %13 : i1
        scf.condition(%14) %arg593, %arg594, %arg595 : tensor<i1>, !jasp.QubitArray, !jasp.QuantumState
      } do {
      ^bb0(%arg590: tensor<i1>, %arg591: !jasp.QubitArray, %arg592: !jasp.QuantumState):
        %15 = jasp.reset %arg591, %arg592 : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
        %16 = jasp.delete_qubits %arg591, %15 : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
        %17, %18, %19 = func.call @lcu_trial(%16) : (!jasp.QuantumState) -> (tensor<i1>, !jasp.QubitArray, !jasp.QuantumState)
        scf.yield %17, %18, %19 : tensor<i1>, !jasp.QubitArray, !jasp.QuantumState
      }
      scf.yield %9, %10, %11 : tensor<i1>, !jasp.QubitArray, !jasp.QuantumState
    } else {
      scf.yield %0, %1, %2 : tensor<i1>, !jasp.QubitArray, !jasp.QuantumState
    }
    %20 = jasp.get_size %7 : !jasp.QubitArray -> tensor<i64>
    %21 = arith.constant 1 : i64
    %22 = tensor.extract %20[] : tensor<i64>
    %23 = arith.subi %22, %21 : i64
    %24 = tensor.from_elements %23 : tensor<i64>
    %25 = arith.subi %23, %23 : i64
    %26 = tensor.from_elements %25 : tensor<i64>
    %27, %28, %29, %30 = scf.while (%arg578 = %7, %arg579 = %24, %arg580 = %26, %arg581 = %8) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %31 = tensor.extract %arg580[] : tensor<i64>
      %32 = tensor.extract %arg579[] : tensor<i64>
      %33 = arith.cmpi sle, %31, %32 : i64
      scf.condition(%33) %arg578, %arg579, %arg580, %arg581 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb1(%arg572: !jasp.QubitArray, %arg573: tensor<i64>, %arg574: tensor<i64>, %arg575: !jasp.QuantumState):
      %34 = jasp.get_qubit %arg572, %arg574 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %35 = jasp.quantum_gate "h" (%34) , %arg575 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %36 = arith.constant 1 : i64
      %37 = tensor.extract %arg574[] : tensor<i64>
      %38 = arith.addi %37, %36 : i64
      %39 = tensor.from_elements %38 : tensor<i64>
      %40 = func.call @_jrange_marker(%39, %arg573) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg572, %arg573, %40, %35 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %41 = arith.constant dense<0> : tensor<i64>
    %42 = jasp.get_qubit %7, %41 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %43, %44 = jasp.measure %42, %30 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    func.return %43, %44 : tensor<i1>, !jasp.QuantumState
  }
  func.func private @lcu_trial(%arg548: !jasp.QuantumState) -> (tensor<i1>, !jasp.QubitArray, !jasp.QuantumState) {
    %0 = arith.constant dense<1> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg548 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = jasp.get_size %1 : !jasp.QubitArray -> tensor<i64>
    %4 = arith.constant 1 : i64
    %5 = tensor.extract %3[] : tensor<i64>
    %6 = arith.subi %5, %4 : i64
    %7 = tensor.from_elements %6 : tensor<i64>
    %8 = arith.subi %6, %6 : i64
    %9 = tensor.from_elements %8 : tensor<i64>
    %10, %11, %12, %13 = scf.while (%arg559 = %1, %arg560 = %7, %arg561 = %9, %arg562 = %2) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %14 = tensor.extract %arg561[] : tensor<i64>
      %15 = tensor.extract %arg560[] : tensor<i64>
      %16 = arith.cmpi sle, %14, %15 : i64
      scf.condition(%16) %arg559, %arg560, %arg561, %arg562 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg553: !jasp.QubitArray, %arg554: tensor<i64>, %arg555: tensor<i64>, %arg556: !jasp.QuantumState):
      %17 = jasp.get_qubit %arg553, %arg555 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %18 = jasp.quantum_gate "x" (%17) , %arg556 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %19 = arith.constant 1 : i64
      %20 = tensor.extract %arg555[] : tensor<i64>
      %21 = arith.addi %20, %19 : i64
      %22 = tensor.from_elements %21 : tensor<i64>
      %23 = func.call @_jrange_marker(%22, %arg554) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg553, %arg554, %23, %18 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %24 = arith.constant dense<1> : tensor<i64>
    %25, %26 = jasp.create_qubits %24, %13 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %27 = func.call @conjugation_env(%25, %1, %26) : (!jasp.QubitArray, !jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
    %28 = arith.constant dense<0> : tensor<i64>
    %29 = jasp.get_qubit %25, %28 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %30, %31 = jasp.measure %29, %27 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %32 = tensor.extract %30[] : tensor<i1>
    %33 = arith.constant true
    %34 = arith.xori %32, %33 : i1
    %35 = tensor.from_elements %34 : tensor<i1>
    %36 = jasp.reset %25, %31 : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
    %37 = jasp.delete_qubits %25, %36 : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
    func.return %35, %1, %37 : tensor<i1>, !jasp.QubitArray, !jasp.QuantumState
  }
  func.func private @_jrange_marker(%arg546: tensor<i64>, %arg547: tensor<i64>) -> (tensor<i64>) {
    func.return %arg546 : tensor<i64>
  }
  func.func private @conjugation_env(%arg543: !jasp.QubitArray, %arg544: !jasp.QubitArray, %arg545: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = func.call @eval(%arg543, %arg545) : (!jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
    %1 = arith.constant dense<0> : tensor<i64>
    %2 = func.call @adaptive_inversion_function(%arg543, %1, %arg544, %0) : (!jasp.QubitArray, tensor<i64>, !jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
    %3 = func.call @eval_dg(%arg543, %2) : (!jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
    func.return %3 : !jasp.QuantumState
  }
  func.func private @eval(%arg523: !jasp.QubitArray, %arg524: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.get_size %arg523 : !jasp.QubitArray -> tensor<i64>
    %1 = arith.constant 1 : i64
    %2 = tensor.extract %0[] : tensor<i64>
    %3 = arith.subi %2, %1 : i64
    %4 = tensor.from_elements %3 : tensor<i64>
    %5 = arith.subi %3, %3 : i64
    %6 = tensor.from_elements %5 : tensor<i64>
    %7, %8, %9, %10 = scf.while (%arg531 = %arg523, %arg532 = %4, %arg533 = %6, %arg534 = %arg524) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %11 = tensor.extract %arg533[] : tensor<i64>
      %12 = tensor.extract %arg532[] : tensor<i64>
      %13 = arith.cmpi sle, %11, %12 : i64
      scf.condition(%13) %arg531, %arg532, %arg533, %arg534 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg525: !jasp.QubitArray, %arg526: tensor<i64>, %arg527: tensor<i64>, %arg528: !jasp.QuantumState):
      %14 = jasp.get_qubit %arg525, %arg527 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %15 = jasp.quantum_gate "h" (%14) , %arg528 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %16 = arith.constant 1 : i64
      %17 = tensor.extract %arg527[] : tensor<i64>
      %18 = arith.addi %17, %16 : i64
      %19 = tensor.from_elements %18 : tensor<i64>
      %20 = func.call @_jrange_marker(%19, %arg526) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg525, %arg526, %20, %15 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    func.return %10 : !jasp.QuantumState
  }
  func.func private @adaptive_inversion_function(%arg519: !jasp.QubitArray, %arg520: tensor<i64>, %arg521: !jasp.QubitArray, %arg522: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = func.call @_q_switch_q(%arg519, %arg520, %arg521, %arg522) : (!jasp.QubitArray, tensor<i64>, !jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
    func.return %0 : !jasp.QuantumState
  }
  func.func private @_q_switch_q(%arg124: !jasp.QubitArray, %arg125: tensor<i64>, %arg126: !jasp.QubitArray, %arg127: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.get_size %arg124 : !jasp.QubitArray -> tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg127 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = func.call @tracerizer() : () -> tensor<i64>
    %4 = arith.constant dense<1> : tensor<i64>
    %5 = arith.constant 1 : i64
    %6 = tensor.extract %0[] : tensor<i64>
    %7 = arith.subi %6, %5 : i64
    %8 = tensor.from_elements %7 : tensor<i64>
    %9, %10, %11, %12, %13, %14 = scf.while (%arg508 = %0, %arg509 = %arg124, %arg510 = %1, %arg511 = %8, %arg512 = %3, %arg513 = %2) : (tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %15 = tensor.extract %arg512[] : tensor<i64>
      %16 = tensor.extract %arg511[] : tensor<i64>
      %17 = arith.cmpi sle, %15, %16 : i64
      scf.condition(%17) %arg508, %arg509, %arg510, %arg511, %arg512, %arg513 : tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg472: tensor<i64>, %arg473: !jasp.QubitArray, %arg474: !jasp.QubitArray, %arg475: tensor<i64>, %arg476: tensor<i64>, %arg477: !jasp.QuantumState):
      %18 = arith.constant 1 : i64
      %19 = tensor.extract %arg472[] : tensor<i64>
      %20 = arith.subi %19, %18 : i64
      %21 = tensor.extract %arg476[] : tensor<i64>
      %22 = arith.subi %20, %21 : i64
      %23 = tensor.from_elements %22 : tensor<i64>
      %24 = jasp.get_qubit %arg473, %23 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %25 = jasp.quantum_gate "x" (%24) , %arg477 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %26 = arith.constant 1 : i64
      %27 = tensor.extract %arg476[] : tensor<i64>
      %28 = arith.subi %27, %26 : i64
      %29 = arith.constant -1 : i64
      %30 = arith.cmpi eq, %28, %29 : i64
      %31 = arith.constant true
      %32 = arith.xori %30, %31 : i1
      %33 = scf.if %32 -> (!jasp.QuantumState) {
        %34 = arith.constant 1 : i64
        %35 = tensor.extract %arg472[] : tensor<i64>
        %36 = arith.subi %35, %34 : i64
        %37 = tensor.extract %arg476[] : tensor<i64>
        %38 = arith.subi %36, %37 : i64
        %39 = tensor.from_elements %38 : tensor<i64>
        %40 = jasp.get_qubit %arg473, %39 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %41 = arith.constant 1 : i64
        %42 = tensor.extract %arg476[] : tensor<i64>
        %43 = arith.subi %42, %41 : i64
        %44 = tensor.from_elements %43 : tensor<i64>
        %45 = jasp.get_qubit %arg474, %44 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %46 = jasp.get_qubit %arg474, %arg476 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %47 = jasp.quantum_gate "h" (%46) , %25 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %48 = jasp.quantum_gate "t_dg" (%45) , %47 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %49 = jasp.quantum_gate "t_dg" (%40) , %48 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %50 = jasp.quantum_gate "cx" (%46, %45) , %49 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %51 = jasp.quantum_gate "cx" (%40, %46) , %50 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %52 = jasp.quantum_gate "t" (%45) , %51 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %53 = jasp.quantum_gate "cx" (%40, %45) , %52 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %54 = jasp.quantum_gate "t" (%46) , %53 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %55 = jasp.quantum_gate "cx" (%40, %46) , %54 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %56 = jasp.quantum_gate "t_dg" (%45) , %55 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %57 = jasp.quantum_gate "cx" (%46, %45) , %56 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %58 = jasp.quantum_gate "t" (%45) , %57 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %59 = jasp.quantum_gate "t_dg" (%46) , %58 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %60 = jasp.quantum_gate "cx" (%40, %45) , %59 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %61 = jasp.quantum_gate "h" (%46) , %60 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %61 : !jasp.QuantumState
      } else {
        %62 = arith.constant 1 : i64
        %63 = tensor.extract %arg472[] : tensor<i64>
        %64 = arith.subi %63, %62 : i64
        %65 = tensor.extract %arg476[] : tensor<i64>
        %66 = arith.subi %64, %65 : i64
        %67 = tensor.from_elements %66 : tensor<i64>
        %68 = jasp.get_qubit %arg473, %67 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %69 = jasp.get_qubit %arg474, %arg476 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %70 = jasp.quantum_gate "cx" (%68, %69) , %25 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %70 : !jasp.QuantumState
      }
      %71 = arith.constant 1 : i64
      %72 = tensor.extract %arg472[] : tensor<i64>
      %73 = arith.subi %72, %71 : i64
      %74 = tensor.extract %arg476[] : tensor<i64>
      %75 = arith.subi %73, %74 : i64
      %76 = tensor.from_elements %75 : tensor<i64>
      %77 = jasp.get_qubit %arg473, %76 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %78 = jasp.quantum_gate "x" (%77) , %33 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %79 = arith.constant 1 : i64
      %80 = tensor.extract %arg476[] : tensor<i64>
      %81 = arith.addi %80, %79 : i64
      %82 = tensor.from_elements %81 : tensor<i64>
      %83 = func.call @_jrange_marker(%82, %arg475) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg472, %arg473, %arg474, %arg475, %83, %78 : tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %84 = arith.constant dense<0> : tensor<i64>
    %85, %86, %87, %88, %89, %90, %91, %92 = scf.while (%arg461 = %1, %arg462 = %arg124, %arg463 = %arg125, %arg464 = %arg126, %arg465 = %0, %arg466 = %84, %arg467 = %84, %arg468 = %14) : (!jasp.QubitArray, !jasp.QubitArray, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QubitArray, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %93 = tensor.extract %arg466[] : tensor<i64>
      %94 = tensor.extract %arg467[] : tensor<i64>
      %95 = arith.cmpi slt, %93, %94 : i64
      scf.condition(%95) %arg461, %arg462, %arg463, %arg464, %arg465, %arg466, %arg467, %arg468 : !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb1(%arg282: !jasp.QubitArray, %arg283: !jasp.QubitArray, %arg284: tensor<i64>, %arg285: !jasp.QubitArray, %arg286: tensor<i64>, %arg287: tensor<i64>, %arg288: tensor<i64>, %arg289: !jasp.QuantumState):
      %96 = arith.constant 1 : i64
      %97 = tensor.extract %arg286[] : tensor<i64>
      %98 = arith.subi %97, %96 : i64
      %99 = tensor.from_elements %98 : tensor<i64>
      %100 = arith.constant 2 : i64
      %101 = tensor.extract %arg287[] : tensor<i64>
      %102 = arith.muli %101, %100 : i64
      %103 = arith.constant 0 : i64
      %104 = arith.cmpi eq, %102, %103 : i64
      %105 = arith.constant true
      %106 = arith.xori %104, %105 : i1
      %107 = scf.if %106 -> (!jasp.QuantumState) {
        scf.yield %arg289 : !jasp.QuantumState
      } else {
        %108 = jasp.get_qubit %arg282, %99 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %109 = func.call @ctrl_env(%108, %arg289) : (!jasp.Qubit, !jasp.QuantumState) -> !jasp.QuantumState
        %110 = arith.constant 1 : i64
        %111 = arith.subi %98, %110 : i64
        %112 = arith.constant -1 : i64
        %113 = arith.cmpi eq, %111, %112 : i64
        %114 = arith.constant true
        %115 = arith.xori %113, %114 : i1
        %116 = scf.if %115 -> (!jasp.QuantumState) {
          %117 = arith.constant 1 : i64
          %118 = arith.subi %98, %117 : i64
          %119 = tensor.from_elements %118 : tensor<i64>
          %120 = jasp.get_qubit %arg282, %119 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %121 = jasp.get_qubit %arg282, %99 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %122 = jasp.quantum_gate "cx" (%120, %121) , %109 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %122 : !jasp.QuantumState
        } else {
          %123 = jasp.get_qubit %arg282, %99 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %124 = jasp.quantum_gate "x" (%123) , %109 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %124 : !jasp.QuantumState
        }
        %125 = func.call @ctrl_env_25(%108, %arg285, %116) : (!jasp.Qubit, !jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
        scf.yield %125 : !jasp.QuantumState
      }
      %126 = arith.constant 1 : i64
      %127 = tensor.extract %arg287[] : tensor<i64>
      %128 = arith.addi %127, %126 : i64
      %129 = tensor.extract %arg287[] : tensor<i64>
      %130 = arith.xori %129, %128 : i64
      %131 = tensor.from_elements %130 : tensor<i64>
      %132 = func.call @bitwise_count(%131) : (tensor<i64>) -> tensor<i8>
      %133 = tensor.extract %132[] : tensor<i8>
      %134 = arith.extsi %133 : i8 to i32
      %135 = tensor.from_elements %134 : tensor<i32>
      %136 = arith.constant 1 : i32
      %137 = arith.subi %134, %136 : i32
      %138 = func.call @tracerizer_33() : () -> tensor<i64>
      %139 = arith.extsi %137 : i32 to i64
      %140 = arith.constant 1 : i64
      %141 = arith.subi %139, %140 : i64
      %142 = tensor.from_elements %141 : tensor<i64>
      %143, %144, %145, %146, %147, %148 = scf.while (%arg423 = %arg286, %arg424 = %arg283, %arg425 = %arg282, %arg426 = %142, %arg427 = %138, %arg428 = %107) : (tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
        %149 = tensor.extract %arg427[] : tensor<i64>
        %150 = tensor.extract %arg426[] : tensor<i64>
        %151 = arith.cmpi sle, %149, %150 : i64
        scf.condition(%151) %arg423, %arg424, %arg425, %arg426, %arg427, %arg428 : tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
      } do {
      ^bb2(%arg392: tensor<i64>, %arg393: !jasp.QubitArray, %arg394: !jasp.QubitArray, %arg395: tensor<i64>, %arg396: tensor<i64>, %arg397: !jasp.QuantumState):
        %152 = tensor.extract %arg392[] : tensor<i64>
        %153 = tensor.extract %arg396[] : tensor<i64>
        %154 = arith.subi %152, %153 : i64
        %155 = arith.constant 1 : i64
        %156 = arith.subi %154, %155 : i64
        %157 = tensor.from_elements %156 : tensor<i64>
        %158 = arith.constant 1 : i64
        %159 = arith.subi %156, %158 : i64
        %160 = arith.constant -1 : i64
        %161 = arith.cmpi eq, %159, %160 : i64
        %162 = arith.constant true
        %163 = arith.xori %161, %162 : i1
        %164 = scf.if %163 -> (!jasp.QuantumState) {
          %165 = arith.constant 1 : i64
          %166 = tensor.extract %arg392[] : tensor<i64>
          %167 = arith.subi %166, %165 : i64
          %168 = arith.subi %167, %156 : i64
          %169 = tensor.from_elements %168 : tensor<i64>
          %170 = jasp.get_qubit %arg393, %169 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %171 = arith.constant 1 : i64
          %172 = arith.subi %156, %171 : i64
          %173 = tensor.from_elements %172 : tensor<i64>
          %174 = jasp.get_qubit %arg394, %173 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %175 = jasp.get_qubit %arg394, %157 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %176 = jasp.quantum_gate "h" (%175) , %arg397 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %177 = jasp.quantum_gate "t_dg" (%174) , %176 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %178 = jasp.quantum_gate "t_dg" (%170) , %177 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %179 = jasp.quantum_gate "cx" (%175, %174) , %178 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %180 = jasp.quantum_gate "cx" (%170, %175) , %179 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %181 = jasp.quantum_gate "t" (%174) , %180 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %182 = jasp.quantum_gate "cx" (%170, %174) , %181 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %183 = jasp.quantum_gate "t" (%175) , %182 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %184 = jasp.quantum_gate "cx" (%170, %175) , %183 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %185 = jasp.quantum_gate "t_dg" (%174) , %184 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %186 = jasp.quantum_gate "cx" (%175, %174) , %185 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %187 = jasp.quantum_gate "t" (%174) , %186 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %188 = jasp.quantum_gate "t_dg" (%175) , %187 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %189 = jasp.quantum_gate "cx" (%170, %174) , %188 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %190 = jasp.quantum_gate "h" (%175) , %189 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %190 : !jasp.QuantumState
        } else {
          %191 = arith.constant 1 : i64
          %192 = tensor.extract %arg392[] : tensor<i64>
          %193 = arith.subi %192, %191 : i64
          %194 = arith.subi %193, %156 : i64
          %195 = tensor.from_elements %194 : tensor<i64>
          %196 = jasp.get_qubit %arg393, %195 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %197 = jasp.get_qubit %arg394, %157 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %198 = jasp.quantum_gate "cx" (%196, %197) , %arg397 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %198 : !jasp.QuantumState
        }
        %199 = arith.constant 1 : i64
        %200 = tensor.extract %arg396[] : tensor<i64>
        %201 = arith.addi %200, %199 : i64
        %202 = tensor.from_elements %201 : tensor<i64>
        %203 = func.call @_jrange_marker(%202, %arg395) : (tensor<i64>, tensor<i64>) -> tensor<i64>
        scf.yield %arg392, %arg393, %arg394, %arg395, %203, %164 : tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
      }
      %204 = arith.extsi %134 : i32 to i64
      %205 = tensor.extract %arg286[] : tensor<i64>
      %206 = arith.subi %205, %204 : i64
      %207 = tensor.from_elements %206 : tensor<i64>
      %208 = arith.constant 2 : i64
      %209 = arith.subi %206, %208 : i64
      %210 = arith.constant -1 : i64
      %211 = arith.cmpi eq, %209, %210 : i64
      %212 = arith.constant true
      %213 = arith.xori %211, %212 : i1
      %214 = scf.if %213 -> (!jasp.QuantumState) {
        %215 = arith.constant 2 : i64
        %216 = arith.subi %206, %215 : i64
        %217 = tensor.from_elements %216 : tensor<i64>
        %218 = jasp.get_qubit %arg282, %217 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %219 = arith.constant 1 : i64
        %220 = arith.subi %206, %219 : i64
        %221 = tensor.from_elements %220 : tensor<i64>
        %222 = jasp.get_qubit %arg282, %221 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %223 = jasp.quantum_gate "cx" (%218, %222) , %148 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %223 : !jasp.QuantumState
      } else {
        %224 = arith.constant 1 : i64
        %225 = arith.subi %206, %224 : i64
        %226 = tensor.from_elements %225 : tensor<i64>
        %227 = jasp.get_qubit %arg282, %226 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %228 = jasp.quantum_gate "x" (%227) , %148 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %228 : !jasp.QuantumState
      }
      %229 = arith.constant 1 : i64
      %230 = arith.subi %206, %229 : i64
      %231 = tensor.from_elements %230 : tensor<i64>
      %232 = jasp.get_qubit %arg282, %231 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %233 = func.call @ctrl_env_41(%232, %arg282, %207, %214) : (!jasp.Qubit, !jasp.QubitArray, tensor<i64>, !jasp.QuantumState) -> !jasp.QuantumState
      %234 = arith.constant 2 : i64
      %235 = arith.subi %206, %234 : i64
      %236 = arith.constant -1 : i64
      %237 = arith.cmpi eq, %235, %236 : i64
      %238 = arith.constant true
      %239 = arith.xori %237, %238 : i1
      %240 = scf.if %239 -> (!jasp.QuantumState) {
        %241 = arith.constant 1 : i64
        %242 = tensor.extract %arg286[] : tensor<i64>
        %243 = arith.subi %242, %241 : i64
        %244 = arith.subi %243, %206 : i64
        %245 = tensor.from_elements %244 : tensor<i64>
        %246 = jasp.get_qubit %arg283, %245 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %247 = arith.constant 2 : i64
        %248 = arith.subi %206, %247 : i64
        %249 = tensor.from_elements %248 : tensor<i64>
        %250 = jasp.get_qubit %arg282, %249 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %251 = jasp.get_qubit %arg282, %207 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %252 = jasp.quantum_gate "h" (%251) , %233 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %253 = jasp.quantum_gate "t_dg" (%250) , %252 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %254 = jasp.quantum_gate "t_dg" (%246) , %253 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %255 = jasp.quantum_gate "cx" (%251, %250) , %254 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %256 = jasp.quantum_gate "cx" (%246, %251) , %255 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %257 = jasp.quantum_gate "t" (%250) , %256 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %258 = jasp.quantum_gate "cx" (%246, %250) , %257 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %259 = jasp.quantum_gate "t" (%251) , %258 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %260 = jasp.quantum_gate "cx" (%246, %251) , %259 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %261 = jasp.quantum_gate "t_dg" (%250) , %260 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %262 = jasp.quantum_gate "cx" (%251, %250) , %261 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %263 = jasp.quantum_gate "t" (%250) , %262 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %264 = jasp.quantum_gate "t_dg" (%251) , %263 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %265 = jasp.quantum_gate "cx" (%246, %250) , %264 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %266 = jasp.quantum_gate "h" (%251) , %265 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %266 : !jasp.QuantumState
      } else {
        %267 = arith.constant 1 : i64
        %268 = tensor.extract %arg286[] : tensor<i64>
        %269 = arith.subi %268, %267 : i64
        %270 = arith.subi %269, %206 : i64
        %271 = tensor.from_elements %270 : tensor<i64>
        %272 = jasp.get_qubit %arg283, %271 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %273 = jasp.get_qubit %arg282, %207 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %274 = jasp.quantum_gate "cx" (%272, %273) , %233 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %274 : !jasp.QuantumState
      }
      %275 = arith.constant 1 : i32
      %276 = arith.subi %134, %275 : i32
      %277 = func.call @tracerizer_45() : () -> tensor<i64>
      %278 = arith.extsi %276 : i32 to i64
      %279 = arith.constant 1 : i64
      %280 = arith.subi %278, %279 : i64
      %281 = tensor.from_elements %280 : tensor<i64>
      %282, %283, %284, %285, %286, %287, %288 = scf.while (%arg339 = %135, %arg340 = %arg286, %arg341 = %arg283, %arg342 = %arg282, %arg343 = %281, %arg344 = %277, %arg345 = %240) : (tensor<i32>, tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (tensor<i32>, tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
        %289 = tensor.extract %arg344[] : tensor<i64>
        %290 = tensor.extract %arg343[] : tensor<i64>
        %291 = arith.cmpi sle, %289, %290 : i64
        scf.condition(%291) %arg339, %arg340, %arg341, %arg342, %arg343, %arg344, %arg345 : tensor<i32>, tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
      } do {
      ^bb3(%arg292: tensor<i32>, %arg293: tensor<i64>, %arg294: !jasp.QubitArray, %arg295: !jasp.QubitArray, %arg296: tensor<i64>, %arg297: tensor<i64>, %arg298: !jasp.QuantumState):
        %292 = arith.constant 1 : i32
        %293 = tensor.extract %arg292[] : tensor<i32>
        %294 = arith.subi %293, %292 : i32
        %295 = arith.extsi %294 : i32 to i64
        %296 = tensor.extract %arg293[] : tensor<i64>
        %297 = arith.subi %296, %295 : i64
        %298 = tensor.extract %arg297[] : tensor<i64>
        %299 = arith.addi %297, %298 : i64
        %300 = tensor.from_elements %299 : tensor<i64>
        %301 = arith.constant 1 : i64
        %302 = tensor.extract %arg293[] : tensor<i64>
        %303 = arith.subi %302, %301 : i64
        %304 = arith.subi %303, %299 : i64
        %305 = tensor.from_elements %304 : tensor<i64>
        %306 = jasp.get_qubit %arg294, %305 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %307 = jasp.quantum_gate "x" (%306) , %arg298 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %308 = arith.constant 1 : i64
        %309 = arith.subi %299, %308 : i64
        %310 = arith.constant -1 : i64
        %311 = arith.cmpi eq, %309, %310 : i64
        %312 = arith.constant true
        %313 = arith.xori %311, %312 : i1
        %314 = scf.if %313 -> (!jasp.QuantumState) {
          %315 = arith.constant 1 : i64
          %316 = tensor.extract %arg293[] : tensor<i64>
          %317 = arith.subi %316, %315 : i64
          %318 = arith.subi %317, %299 : i64
          %319 = tensor.from_elements %318 : tensor<i64>
          %320 = jasp.get_qubit %arg294, %319 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %321 = arith.constant 1 : i64
          %322 = arith.subi %299, %321 : i64
          %323 = tensor.from_elements %322 : tensor<i64>
          %324 = jasp.get_qubit %arg295, %323 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %325 = jasp.get_qubit %arg295, %300 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %326 = jasp.quantum_gate "h" (%325) , %307 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %327 = jasp.quantum_gate "t_dg" (%324) , %326 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %328 = jasp.quantum_gate "t_dg" (%320) , %327 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %329 = jasp.quantum_gate "cx" (%325, %324) , %328 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %330 = jasp.quantum_gate "cx" (%320, %325) , %329 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %331 = jasp.quantum_gate "t" (%324) , %330 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %332 = jasp.quantum_gate "cx" (%320, %324) , %331 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %333 = jasp.quantum_gate "t" (%325) , %332 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %334 = jasp.quantum_gate "cx" (%320, %325) , %333 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %335 = jasp.quantum_gate "t_dg" (%324) , %334 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %336 = jasp.quantum_gate "cx" (%325, %324) , %335 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %337 = jasp.quantum_gate "t" (%324) , %336 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %338 = jasp.quantum_gate "t_dg" (%325) , %337 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %339 = jasp.quantum_gate "cx" (%320, %324) , %338 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          %340 = jasp.quantum_gate "h" (%325) , %339 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %340 : !jasp.QuantumState
        } else {
          %341 = arith.constant 1 : i64
          %342 = tensor.extract %arg293[] : tensor<i64>
          %343 = arith.subi %342, %341 : i64
          %344 = arith.subi %343, %299 : i64
          %345 = tensor.from_elements %344 : tensor<i64>
          %346 = jasp.get_qubit %arg294, %345 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %347 = jasp.get_qubit %arg295, %300 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %348 = jasp.quantum_gate "cx" (%346, %347) , %307 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %348 : !jasp.QuantumState
        }
        %349 = arith.constant 1 : i64
        %350 = tensor.extract %arg293[] : tensor<i64>
        %351 = arith.subi %350, %349 : i64
        %352 = arith.subi %351, %299 : i64
        %353 = tensor.from_elements %352 : tensor<i64>
        %354 = jasp.get_qubit %arg294, %353 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %355 = jasp.quantum_gate "x" (%354) , %314 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %356 = arith.constant 1 : i64
        %357 = tensor.extract %arg297[] : tensor<i64>
        %358 = arith.addi %357, %356 : i64
        %359 = tensor.from_elements %358 : tensor<i64>
        %360 = func.call @_jrange_marker(%359, %arg296) : (tensor<i64>, tensor<i64>) -> tensor<i64>
        scf.yield %arg292, %arg293, %arg294, %arg295, %arg296, %360, %355 : tensor<i32>, tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
      }
      %361 = arith.constant 1 : i64
      %362 = tensor.extract %arg287[] : tensor<i64>
      %363 = arith.addi %362, %361 : i64
      %364 = tensor.from_elements %363 : tensor<i64>
      scf.yield %arg282, %arg283, %arg284, %arg285, %arg286, %364, %arg288, %288 : !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %365 = arith.constant dense<1> : tensor<i32>
    %366 = tensor.extract %365[] : tensor<i32>
    %367 = arith.constant 0 : i32
    %368 = arith.cmpi eq, %366, %367 : i32
    %369 = scf.if %368 -> (!jasp.QuantumState) {
      %370 = arith.constant 1 : i64
      %371 = tensor.extract %0[] : tensor<i64>
      %372 = arith.subi %371, %370 : i64
      %373 = tensor.from_elements %372 : tensor<i64>
      %374 = arith.constant dense<0> : tensor<i32>
      %375 = tensor.extract %374[] : tensor<i32>
      %376 = arith.constant 0 : i32
      %377 = arith.cmpi eq, %375, %376 : i32
      %378 = scf.if %377 -> (!jasp.QuantumState) {
        scf.yield %92 : !jasp.QuantumState
      } else {
        %379 = jasp.get_qubit %1, %373 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %380 = func.call @ctrl_env_53(%379, %92) : (!jasp.Qubit, !jasp.QuantumState) -> !jasp.QuantumState
        scf.yield %380 : !jasp.QuantumState
      }
      %381 = arith.constant dense<1> : tensor<i32>
      %382 = tensor.extract %381[] : tensor<i32>
      %383 = arith.constant 0 : i32
      %384 = arith.cmpi eq, %382, %383 : i32
      %385 = scf.if %384 -> (!jasp.QuantumState) {
        scf.yield %378 : !jasp.QuantumState
      } else {
        %386 = jasp.get_qubit %1, %373 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %387 = func.call @ctrl_env_55(%386, %arg126, %378) : (!jasp.Qubit, !jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
        scf.yield %387 : !jasp.QuantumState
      }
      scf.yield %385 : !jasp.QuantumState
    } else {
      %388 = arith.constant 1 : i64
      %389 = tensor.extract %0[] : tensor<i64>
      %390 = arith.subi %389, %388 : i64
      %391 = tensor.from_elements %390 : tensor<i64>
      %392 = arith.constant dense<1> : tensor<i32>
      %393 = tensor.extract %392[] : tensor<i32>
      %394 = arith.constant 0 : i32
      %395 = arith.cmpi eq, %393, %394 : i32
      %396 = scf.if %395 -> (!jasp.QuantumState) {
        scf.yield %92 : !jasp.QuantumState
      } else {
        %397 = jasp.get_qubit %1, %391 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %398 = func.call @ctrl_env_59(%397, %92) : (!jasp.Qubit, !jasp.QuantumState) -> !jasp.QuantumState
        %399 = arith.constant 1 : i64
        %400 = arith.subi %390, %399 : i64
        %401 = arith.constant -1 : i64
        %402 = arith.cmpi eq, %400, %401 : i64
        %403 = arith.constant true
        %404 = arith.xori %402, %403 : i1
        %405 = scf.if %404 -> (!jasp.QuantumState) {
          %406 = arith.constant 1 : i64
          %407 = arith.subi %390, %406 : i64
          %408 = tensor.from_elements %407 : tensor<i64>
          %409 = jasp.get_qubit %1, %408 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %410 = jasp.get_qubit %1, %391 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %411 = jasp.quantum_gate "cx" (%409, %410) , %398 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %411 : !jasp.QuantumState
        } else {
          %412 = jasp.get_qubit %1, %391 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %413 = jasp.quantum_gate "x" (%412) , %398 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %413 : !jasp.QuantumState
        }
        %414 = func.call @ctrl_env_63(%397, %arg126, %405) : (!jasp.Qubit, !jasp.QubitArray, !jasp.QuantumState) -> !jasp.QuantumState
        scf.yield %414 : !jasp.QuantumState
      }
      scf.yield %396 : !jasp.QuantumState
    }
    %415 = arith.constant 2 : i64
    %416 = arith.constant 0 : i64
    %417 = arith.cmpi eq, %415, %416 : i64
    %418 = arith.constant 0 : i64
    %419 = tensor.extract %0[] : tensor<i64>
    %420 = arith.cmpi ne, %419, %418 : i64
    %421 = arith.andi %417, %420 : i1
    %422 = tensor.from_elements %421 : tensor<i1>
    %423 = func.call @_where(%422, %84, %4) : (tensor<i1>, tensor<i64>, tensor<i64>) -> tensor<i64>
    %424 = arith.constant 1 : i64
    %425 = tensor.extract %0[] : tensor<i64>
    %426 = arith.andi %425, %424 : i64
    %427 = tensor.from_elements %426 : tensor<i64>
    %428 = arith.constant 2 : i64
    %429 = tensor.extract %423[] : tensor<i64>
    %430 = arith.muli %429, %428 : i64
    %431 = tensor.from_elements %430 : tensor<i64>
    %432 = func.call @_where_68(%427, %431, %423) : (tensor<i64>, tensor<i64>, tensor<i64>) -> tensor<i64>
    %433 = arith.constant 4 : i64
    %434 = arith.constant 1 : i64
    %435 = tensor.extract %0[] : tensor<i64>
    %436 = arith.constant 0 : i64
    %437 = arith.shrui %435, %434 : i64
    %438 = arith.constant 64 : i64
    %439 = arith.cmpi ugt, %438, %434 : i64
    %440 = arith.select %439, %437, %436 : i64
    %441 = arith.constant 1 : i64
    %442 = arith.andi %440, %441 : i64
    %443 = tensor.from_elements %442 : tensor<i64>
    %444 = tensor.extract %432[] : tensor<i64>
    %445 = arith.muli %444, %433 : i64
    %446 = tensor.from_elements %445 : tensor<i64>
    %447 = func.call @_where_68(%443, %446, %432) : (tensor<i64>, tensor<i64>, tensor<i64>) -> tensor<i64>
    %448 = arith.constant 16 : i64
    %449 = arith.constant 1 : i64
    %450 = arith.constant 0 : i64
    %451 = arith.shrui %440, %449 : i64
    %452 = arith.constant 64 : i64
    %453 = arith.cmpi ugt, %452, %449 : i64
    %454 = arith.select %453, %451, %450 : i64
    %455 = arith.constant 1 : i64
    %456 = arith.andi %454, %455 : i64
    %457 = tensor.from_elements %456 : tensor<i64>
    %458 = tensor.extract %447[] : tensor<i64>
    %459 = arith.muli %458, %448 : i64
    %460 = tensor.from_elements %459 : tensor<i64>
    %461 = func.call @_where_68(%457, %460, %447) : (tensor<i64>, tensor<i64>, tensor<i64>) -> tensor<i64>
    %462 = arith.constant 256 : i64
    %463 = arith.constant 1 : i64
    %464 = arith.constant 0 : i64
    %465 = arith.shrui %454, %463 : i64
    %466 = arith.constant 64 : i64
    %467 = arith.cmpi ugt, %466, %463 : i64
    %468 = arith.select %467, %465, %464 : i64
    %469 = arith.constant 1 : i64
    %470 = arith.andi %468, %469 : i64
    %471 = tensor.from_elements %470 : tensor<i64>
    %472 = tensor.extract %461[] : tensor<i64>
    %473 = arith.muli %472, %462 : i64
    %474 = tensor.from_elements %473 : tensor<i64>
    %475 = func.call @_where_68(%471, %474, %461) : (tensor<i64>, tensor<i64>, tensor<i64>) -> tensor<i64>
    %476 = arith.constant 65536 : i64
    %477 = arith.constant 1 : i64
    %478 = arith.constant 0 : i64
    %479 = arith.shrui %468, %477 : i64
    %480 = arith.constant 64 : i64
    %481 = arith.cmpi ugt, %480, %477 : i64
    %482 = arith.select %481, %479, %478 : i64
    %483 = arith.constant 1 : i64
    %484 = arith.andi %482, %483 : i64
    %485 = tensor.from_elements %484 : tensor<i64>
    %486 = tensor.extract %475[] : tensor<i64>
    %487 = arith.muli %486, %476 : i64
    %488 = tensor.from_elements %487 : tensor<i64>
    %489 = func.call @_where_68(%485, %488, %475) : (tensor<i64>, tensor<i64>, tensor<i64>) -> tensor<i64>
    %490 = arith.constant 4294967296 : i64
    %491 = arith.constant 1 : i64
    %492 = arith.constant 0 : i64
    %493 = arith.shrui %482, %491 : i64
    %494 = arith.constant 64 : i64
    %495 = arith.cmpi ugt, %494, %491 : i64
    %496 = arith.select %495, %493, %492 : i64
    %497 = arith.constant 1 : i64
    %498 = arith.andi %496, %497 : i64
    %499 = tensor.from_elements %498 : tensor<i64>
    %500 = tensor.extract %489[] : tensor<i64>
    %501 = arith.muli %500, %490 : i64
    %502 = tensor.from_elements %501 : tensor<i64>
    %503 = func.call @_where_68(%499, %502, %489) : (tensor<i64>, tensor<i64>, tensor<i64>) -> tensor<i64>
    %504 = arith.constant 2 : i64
    %505 = tensor.extract %503[] : tensor<i64>
    %506 = arith.subi %505, %504 : i64
    %507 = tensor.from_elements %506 : tensor<i64>
    %508 = func.call @tracerizer_69() : () -> tensor<i64>
    %509 = arith.constant 1 : i64
    %510 = tensor.extract %0[] : tensor<i64>
    %511 = arith.subi %510, %509 : i64
    %512 = tensor.from_elements %511 : tensor<i64>
    %513, %514, %515, %516, %517, %518, %519 = scf.while (%arg193 = %0, %arg194 = %arg124, %arg195 = %1, %arg196 = %507, %arg197 = %512, %arg198 = %508, %arg199 = %369) : (tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %520 = tensor.extract %arg198[] : tensor<i64>
      %521 = tensor.extract %arg197[] : tensor<i64>
      %522 = arith.cmpi sle, %520, %521 : i64
      scf.condition(%522) %arg193, %arg194, %arg195, %arg196, %arg197, %arg198, %arg199 : tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb4(%arg128: tensor<i64>, %arg129: !jasp.QubitArray, %arg130: !jasp.QubitArray, %arg131: tensor<i64>, %arg132: tensor<i64>, %arg133: tensor<i64>, %arg134: !jasp.QuantumState):
      %523 = tensor.extract %arg128[] : tensor<i64>
      %524 = tensor.extract %arg133[] : tensor<i64>
      %525 = arith.subi %523, %524 : i64
      %526 = arith.constant 1 : i64
      %527 = arith.subi %525, %526 : i64
      %528 = tensor.from_elements %527 : tensor<i64>
      %529 = arith.constant 1 : i64
      %530 = arith.subi %527, %529 : i64
      %531 = arith.constant -1 : i64
      %532 = arith.cmpi eq, %530, %531 : i64
      %533 = arith.constant true
      %534 = arith.xori %532, %533 : i1
      %535 = scf.if %534 -> (!jasp.QuantumState) {
        %536 = arith.constant 1 : i64
        %537 = tensor.extract %arg128[] : tensor<i64>
        %538 = arith.subi %537, %536 : i64
        %539 = arith.subi %538, %527 : i64
        %540 = tensor.from_elements %539 : tensor<i64>
        %541 = jasp.get_qubit %arg129, %540 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %542 = arith.constant 1 : i64
        %543 = arith.subi %527, %542 : i64
        %544 = tensor.from_elements %543 : tensor<i64>
        %545 = jasp.get_qubit %arg130, %544 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %546 = jasp.get_qubit %arg130, %528 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %547 = jasp.quantum_gate "h" (%546) , %arg134 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %548 = jasp.quantum_gate "t_dg" (%545) , %547 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %549 = jasp.quantum_gate "t_dg" (%541) , %548 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %550 = jasp.quantum_gate "cx" (%546, %545) , %549 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %551 = jasp.quantum_gate "cx" (%541, %546) , %550 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %552 = jasp.quantum_gate "t" (%545) , %551 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %553 = jasp.quantum_gate "cx" (%541, %545) , %552 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %554 = jasp.quantum_gate "t" (%546) , %553 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %555 = jasp.quantum_gate "cx" (%541, %546) , %554 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %556 = jasp.quantum_gate "t_dg" (%545) , %555 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %557 = jasp.quantum_gate "cx" (%546, %545) , %556 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %558 = jasp.quantum_gate "t" (%545) , %557 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %559 = jasp.quantum_gate "t_dg" (%546) , %558 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %560 = jasp.quantum_gate "cx" (%541, %545) , %559 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %561 = jasp.quantum_gate "h" (%546) , %560 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %561 : !jasp.QuantumState
      } else {
        %562 = arith.constant 1 : i64
        %563 = tensor.extract %arg128[] : tensor<i64>
        %564 = arith.subi %563, %562 : i64
        %565 = arith.subi %564, %527 : i64
        %566 = tensor.from_elements %565 : tensor<i64>
        %567 = jasp.get_qubit %arg129, %566 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %568 = jasp.get_qubit %arg130, %528 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %569 = jasp.quantum_gate "cx" (%567, %568) , %arg134 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %569 : !jasp.QuantumState
      }
      %570 = tensor.extract %arg131[] : tensor<i64>
      %571 = tensor.extract %arg133[] : tensor<i64>
      %572 = arith.constant 63 : i64
      %573 = arith.shrsi %570, %572 : i64
      %574 = arith.shrsi %570, %571 : i64
      %575 = arith.constant 64 : i64
      %576 = arith.cmpi ugt, %575, %571 : i64
      %577 = arith.select %576, %574, %573 : i64
      %578 = arith.constant 1 : i64
      %579 = arith.andi %577, %578 : i64
      %580 = arith.constant 0 : i64
      %581 = arith.cmpi ne, %579, %580 : i64
      %582 = arith.constant true
      %583 = arith.xori %581, %582 : i1
      %584 = scf.if %583 -> (!jasp.QuantumState) {
        scf.yield %535 : !jasp.QuantumState
      } else {
        %585 = tensor.extract %arg128[] : tensor<i64>
        %586 = tensor.extract %arg133[] : tensor<i64>
        %587 = arith.subi %585, %586 : i64
        %588 = arith.constant 2 : i64
        %589 = arith.subi %587, %588 : i64
        %590 = arith.constant -1 : i64
        %591 = arith.cmpi eq, %589, %590 : i64
        %592 = arith.constant true
        %593 = arith.xori %591, %592 : i1
        %594 = scf.if %593 -> (!jasp.QuantumState) {
          %595 = tensor.extract %arg128[] : tensor<i64>
          %596 = tensor.extract %arg133[] : tensor<i64>
          %597 = arith.subi %595, %596 : i64
          %598 = arith.constant 2 : i64
          %599 = arith.subi %597, %598 : i64
          %600 = tensor.from_elements %599 : tensor<i64>
          %601 = jasp.get_qubit %arg130, %600 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %602 = tensor.extract %arg128[] : tensor<i64>
          %603 = tensor.extract %arg133[] : tensor<i64>
          %604 = arith.subi %602, %603 : i64
          %605 = arith.constant 1 : i64
          %606 = arith.subi %604, %605 : i64
          %607 = tensor.from_elements %606 : tensor<i64>
          %608 = jasp.get_qubit %arg130, %607 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %609 = jasp.quantum_gate "cx" (%601, %608) , %535 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %609 : !jasp.QuantumState
        } else {
          %610 = tensor.extract %arg128[] : tensor<i64>
          %611 = tensor.extract %arg133[] : tensor<i64>
          %612 = arith.subi %610, %611 : i64
          %613 = arith.constant 1 : i64
          %614 = arith.subi %612, %613 : i64
          %615 = tensor.from_elements %614 : tensor<i64>
          %616 = jasp.get_qubit %arg130, %615 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %617 = jasp.quantum_gate "x" (%616) , %535 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %617 : !jasp.QuantumState
        }
        scf.yield %594 : !jasp.QuantumState
      }
      %618 = arith.constant 1 : i64
      %619 = tensor.extract %arg133[] : tensor<i64>
      %620 = arith.addi %619, %618 : i64
      %621 = tensor.from_elements %620 : tensor<i64>
      %622 = func.call @_jrange_marker(%621, %arg132) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg128, %arg129, %arg130, %arg131, %arg132, %622, %584 : tensor<i64>, !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    %623 = jasp.delete_qubits %1, %519 : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
    func.return %623 : !jasp.QuantumState
  }
  func.func private @tracerizer() -> (tensor<i64>) {
    %0 = arith.constant dense<0> : tensor<i64>
    func.return %0 : tensor<i64>
  }
  func.func private @ctrl_env(%arg122: !jasp.Qubit, %arg123: !jasp.QuantumState) -> (!jasp.QuantumState) {
    func.return %arg123 : !jasp.QuantumState
  }
  func.func private @ctrl_env_25(%arg99: !jasp.Qubit, %arg100: !jasp.QubitArray, %arg101: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.get_size %arg100 : !jasp.QubitArray -> tensor<i64>
    %1 = arith.constant 1 : i64
    %2 = tensor.extract %0[] : tensor<i64>
    %3 = arith.subi %2, %1 : i64
    %4 = tensor.from_elements %3 : tensor<i64>
    %5 = arith.subi %3, %3 : i64
    %6 = tensor.from_elements %5 : tensor<i64>
    %7, %8, %9, %10, %11 = scf.while (%arg109 = %arg99, %arg110 = %arg100, %arg111 = %4, %arg112 = %6, %arg113 = %arg101) : (!jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %12 = tensor.extract %arg112[] : tensor<i64>
      %13 = tensor.extract %arg111[] : tensor<i64>
      %14 = arith.cmpi sle, %12, %13 : i64
      scf.condition(%14) %arg109, %arg110, %arg111, %arg112, %arg113 : !jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg102: !jasp.Qubit, %arg103: !jasp.QubitArray, %arg104: tensor<i64>, %arg105: tensor<i64>, %arg106: !jasp.QuantumState):
      %15 = jasp.get_qubit %arg103, %arg105 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %16 = jasp.quantum_gate "cx" (%arg102, %15) , %arg106 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %17 = arith.constant 1 : i64
      %18 = tensor.extract %arg105[] : tensor<i64>
      %19 = arith.addi %18, %17 : i64
      %20 = tensor.from_elements %19 : tensor<i64>
      %21 = func.call @_jrange_marker_28(%20, %arg104) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg102, %arg103, %arg104, %21, %16 : !jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    func.return %11 : !jasp.QuantumState
  }
  func.func private @_jrange_marker_28(%arg97: tensor<i64>, %arg98: tensor<i64>) -> (tensor<i64>) {
    func.return %arg97 : tensor<i64>
  }
  func.func private @bitwise_count(%arg90: tensor<i64>) -> (tensor<i8>) {
    %0 = tensor.extract %arg90[] : tensor<i64>
    %1 = arith.constant 0 : i64
    %2 = arith.cmpi sge, %0, %1 : i64
    %3 = arith.subi %1, %0 : i64
    %4 = arith.select %2, %0, %3 : i64
    %5 = math.ctpop %4 : i64
    %6 = arith.trunci %5 : i64 to i8
    %7 = tensor.from_elements %6 : tensor<i8>
    func.return %7 : tensor<i8>
  }
  func.func private @tracerizer_33() -> (tensor<i64>) {
    %0 = arith.constant dense<0> : tensor<i64>
    func.return %0 : tensor<i64>
  }
  func.func private @ctrl_env_41(%arg86: !jasp.Qubit, %arg87: !jasp.QubitArray, %arg88: tensor<i64>, %arg89: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.get_qubit %arg87, %arg88 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %1 = jasp.quantum_gate "cx" (%arg86, %0) , %arg89 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    func.return %1 : !jasp.QuantumState
  }
  func.func private @tracerizer_45() -> (tensor<i64>) {
    %0 = arith.constant dense<0> : tensor<i64>
    func.return %0 : tensor<i64>
  }
  func.func private @ctrl_env_53(%arg84: !jasp.Qubit, %arg85: !jasp.QuantumState) -> (!jasp.QuantumState) {
    func.return %arg85 : !jasp.QuantumState
  }
  func.func private @ctrl_env_55(%arg61: !jasp.Qubit, %arg62: !jasp.QubitArray, %arg63: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.get_size %arg62 : !jasp.QubitArray -> tensor<i64>
    %1 = arith.constant 1 : i64
    %2 = tensor.extract %0[] : tensor<i64>
    %3 = arith.subi %2, %1 : i64
    %4 = tensor.from_elements %3 : tensor<i64>
    %5 = arith.subi %3, %3 : i64
    %6 = tensor.from_elements %5 : tensor<i64>
    %7, %8, %9, %10, %11 = scf.while (%arg71 = %arg61, %arg72 = %arg62, %arg73 = %4, %arg74 = %6, %arg75 = %arg63) : (!jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %12 = tensor.extract %arg74[] : tensor<i64>
      %13 = tensor.extract %arg73[] : tensor<i64>
      %14 = arith.cmpi sle, %12, %13 : i64
      scf.condition(%14) %arg71, %arg72, %arg73, %arg74, %arg75 : !jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg64: !jasp.Qubit, %arg65: !jasp.QubitArray, %arg66: tensor<i64>, %arg67: tensor<i64>, %arg68: !jasp.QuantumState):
      %15 = jasp.get_qubit %arg65, %arg67 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %16 = jasp.quantum_gate "cx" (%arg64, %15) , %arg68 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %17 = arith.constant 1 : i64
      %18 = tensor.extract %arg67[] : tensor<i64>
      %19 = arith.addi %18, %17 : i64
      %20 = tensor.from_elements %19 : tensor<i64>
      %21 = func.call @_jrange_marker_28(%20, %arg66) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg64, %arg65, %arg66, %21, %16 : !jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    func.return %11 : !jasp.QuantumState
  }
  func.func private @ctrl_env_59(%arg59: !jasp.Qubit, %arg60: !jasp.QuantumState) -> (!jasp.QuantumState) {
    func.return %arg60 : !jasp.QuantumState
  }
  func.func private @ctrl_env_63(%arg36: !jasp.Qubit, %arg37: !jasp.QubitArray, %arg38: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.get_size %arg37 : !jasp.QubitArray -> tensor<i64>
    %1 = arith.constant 1 : i64
    %2 = tensor.extract %0[] : tensor<i64>
    %3 = arith.subi %2, %1 : i64
    %4 = tensor.from_elements %3 : tensor<i64>
    %5 = arith.subi %3, %3 : i64
    %6 = tensor.from_elements %5 : tensor<i64>
    %7, %8, %9, %10, %11 = scf.while (%arg46 = %arg36, %arg47 = %arg37, %arg48 = %4, %arg49 = %6, %arg50 = %arg38) : (!jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %12 = tensor.extract %arg49[] : tensor<i64>
      %13 = tensor.extract %arg48[] : tensor<i64>
      %14 = arith.cmpi sle, %12, %13 : i64
      scf.condition(%14) %arg46, %arg47, %arg48, %arg49, %arg50 : !jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg39: !jasp.Qubit, %arg40: !jasp.QubitArray, %arg41: tensor<i64>, %arg42: tensor<i64>, %arg43: !jasp.QuantumState):
      %15 = jasp.get_qubit %arg40, %arg42 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %16 = jasp.quantum_gate "cx" (%arg39, %15) , %arg43 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %17 = arith.constant 1 : i64
      %18 = tensor.extract %arg42[] : tensor<i64>
      %19 = arith.addi %18, %17 : i64
      %20 = tensor.from_elements %19 : tensor<i64>
      %21 = func.call @_jrange_marker_28(%20, %arg41) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg39, %arg40, %arg41, %21, %16 : !jasp.Qubit, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    func.return %11 : !jasp.QuantumState
  }
  func.func private @_where(%arg29: tensor<i1>, %arg30: tensor<i64>, %arg31: tensor<i64>) -> (tensor<i64>) {
    %0 = tensor.extract %arg29[] : tensor<i1>
    %1 = tensor.extract %arg30[] : tensor<i64>
    %2 = tensor.extract %arg31[] : tensor<i64>
    %3 = arith.select %0, %1, %2 : i64
    %4 = tensor.from_elements %3 : tensor<i64>
    func.return %4 : tensor<i64>
  }
  func.func private @_where_68(%arg20: tensor<i64>, %arg21: tensor<i64>, %arg22: tensor<i64>) -> (tensor<i64>) {
    %0 = arith.constant 0 : i64
    %1 = tensor.extract %arg20[] : tensor<i64>
    %2 = arith.cmpi ne, %1, %0 : i64
    %3 = tensor.extract %arg21[] : tensor<i64>
    %4 = tensor.extract %arg22[] : tensor<i64>
    %5 = arith.select %2, %3, %4 : i64
    %6 = tensor.from_elements %5 : tensor<i64>
    func.return %6 : tensor<i64>
  }
  func.func private @tracerizer_69() -> (tensor<i64>) {
    %0 = arith.constant dense<0> : tensor<i64>
    func.return %0 : tensor<i64>
  }
  func.func private @eval_dg(%arg0: !jasp.QubitArray, %arg1: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.get_size %arg0 : !jasp.QubitArray -> tensor<i64>
    %1 = arith.constant 1 : i64
    %2 = tensor.extract %0[] : tensor<i64>
    %3 = arith.subi %2, %1 : i64
    %4 = tensor.from_elements %3 : tensor<i64>
    %5 = arith.subi %3, %3 : i64
    %6 = tensor.from_elements %5 : tensor<i64>
    %7, %8, %9, %10 = scf.while (%arg8 = %arg0, %arg9 = %6, %arg10 = %4, %arg11 = %arg1) : (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %11 = tensor.extract %arg9[] : tensor<i64>
      %12 = tensor.extract %arg10[] : tensor<i64>
      %13 = arith.cmpi sle, %11, %12 : i64
      scf.condition(%13) %arg8, %arg9, %arg10, %arg11 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb0(%arg2: !jasp.QubitArray, %arg3: tensor<i64>, %arg4: tensor<i64>, %arg5: !jasp.QuantumState):
      %14 = jasp.get_qubit %arg2, %arg4 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %15 = arith.constant 1 : i64
      %16 = tensor.extract %arg4[] : tensor<i64>
      %17 = arith.subi %16, %15 : i64
      %18 = tensor.from_elements %17 : tensor<i64>
      %19 = func.call @_jrange_marker(%18, %arg3) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      %20 = jasp.quantum_gate "h" (%14) , %arg5 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %arg2, %arg3, %19, %20 : !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    func.return %10 : !jasp.QuantumState
  }
}
