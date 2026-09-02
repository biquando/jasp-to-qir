builtin.module @jasp_module {
  func.func public @main(%arg187: !jasp.QuantumState) -> (!jasp.QubitArray, tensor<i64>, !jasp.QuantumState) {
    %0 = arith.constant dense<3> : tensor<i64>
    %1, %2 = jasp.create_qubits %0, %arg187 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
    %3 = arith.constant dense<0> : tensor<i64>
    %4 = jasp.get_qubit %1, %3 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
    %5 = jasp.quantum_gate "h" (%4) , %2 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = jasp.get_size %1 : !jasp.QubitArray -> tensor<i64>
    %7 = arith.constant 3.000000e+00 : f64
    %8 = arith.fptosi %7 : f64 to i64
    %9 = tensor.from_elements %8 : tensor<i64>
    %10 = func.call @gidney_adder(%9, %1, %3, %5) : (tensor<i64>, !jasp.QubitArray, tensor<i64>, !jasp.QuantumState) -> !jasp.QuantumState
    func.return %1, %3, %10 : !jasp.QubitArray, tensor<i64>, !jasp.QuantumState
  }
  func.func private @gidney_adder(%arg20: tensor<i64>, %arg21: !jasp.QubitArray, %arg22: tensor<i64>, %arg23: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.get_size %arg21 : !jasp.QubitArray -> tensor<i64>
    %1 = arith.constant dense<0> : tensor<i64>
    %2 = jasp.slice %arg21, %1, %0 : !jasp.QubitArray, tensor<i64>, tensor<i64> -> !jasp.QubitArray
    %3 = jasp.get_size %2 : !jasp.QubitArray -> tensor<i64>
    %4 = arith.constant 1 : i64
    %5 = tensor.extract %3[] : tensor<i64>
    %6 = arith.cmpi sgt, %5, %4 : i64
    %7 = arith.constant true
    %8 = arith.xori %6, %7 : i1
    %9 = scf.if %8 -> (!jasp.QuantumState) {
      scf.yield %arg23 : !jasp.QuantumState
    } else {
      %10 = arith.constant 1 : i64
      %11 = tensor.extract %3[] : tensor<i64>
      %12 = arith.subi %11, %10 : i64
      %13 = tensor.from_elements %12 : tensor<i64>
      %14, %15 = jasp.create_qubits %13, %arg23 : !jasp.QuantumState, tensor<i64> -> !jasp.QubitArray, !jasp.QuantumState
      %16 = arith.constant 0 : i64
      %17 = tensor.extract %arg20[] : tensor<i64>
      %18 = arith.constant 63 : i64
      %19 = arith.shrsi %17, %18 : i64
      %20 = arith.constant 64 : i64
      %21 = arith.cmpi ugt, %20, %16 : i64
      %22 = arith.select %21, %17, %19 : i64
      %23 = arith.constant 1 : i64
      %24 = arith.andi %22, %23 : i64
      %25 = arith.constant dense<0> : tensor<i64>
      %26 = tensor.extract %25[] : tensor<i64>
      %27 = arith.cmpi ne, %24, %26 : i64
      %28 = arith.constant false
      %29 = arith.cmpi ne, %27, %28 : i1
      %30 = arith.constant true
      %31 = arith.xori %29, %30 : i1
      %32 = scf.if %31 -> (!jasp.QuantumState) {
        scf.yield %15 : !jasp.QuantumState
      } else {
        %33 = arith.constant dense<0> : tensor<i64>
        %34 = jasp.get_qubit %2, %33 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %35 = jasp.get_qubit %14, %33 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %36 = jasp.quantum_gate "cx" (%34, %35) , %15 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %36 : !jasp.QuantumState
      }
      %37 = arith.constant 2 : i64
      %38 = tensor.extract %3[] : tensor<i64>
      %39 = arith.subi %38, %37 : i64
      %40 = arith.constant 1 : i64
      %41 = arith.subi %39, %40 : i64
      %42 = tensor.from_elements %41 : tensor<i64>
      %43 = arith.subi %41, %41 : i64
      %44 = tensor.from_elements %43 : tensor<i64>
      %45, %46, %47, %48, %49, %50 = scf.while (%arg152 = %14, %arg153 = %2, %arg154 = %arg20, %arg155 = %42, %arg156 = %44, %arg157 = %32) : (!jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (!jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
        %51 = tensor.extract %arg156[] : tensor<i64>
        %52 = tensor.extract %arg155[] : tensor<i64>
        %53 = arith.cmpi sle, %51, %52 : i64
        scf.condition(%53) %arg152, %arg153, %arg154, %arg155, %arg156, %arg157 : !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState
      } do {
      ^bb0(%arg116: !jasp.QubitArray, %arg117: !jasp.QubitArray, %arg118: tensor<i64>, %arg119: tensor<i64>, %arg120: tensor<i64>, %arg121: !jasp.QuantumState):
        %54 = arith.constant 1 : i64
        %55 = tensor.extract %arg120[] : tensor<i64>
        %56 = arith.addi %55, %54 : i64
        %57 = tensor.from_elements %56 : tensor<i64>
        %58 = arith.constant 1 : i64
        %59 = arith.subi %56, %58 : i64
        %60 = tensor.from_elements %59 : tensor<i64>
        %61 = jasp.get_qubit %arg116, %60 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %62 = jasp.get_qubit %arg117, %57 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %63 = jasp.quantum_gate "cx" (%61, %62) , %arg121 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %64 = tensor.extract %arg118[] : tensor<i64>
        %65 = arith.constant 63 : i64
        %66 = arith.shrsi %64, %65 : i64
        %67 = arith.shrsi %64, %56 : i64
        %68 = arith.constant 64 : i64
        %69 = arith.cmpi ugt, %68, %56 : i64
        %70 = arith.select %69, %67, %66 : i64
        %71 = arith.constant 1 : i64
        %72 = arith.andi %70, %71 : i64
        %73 = arith.constant dense<0> : tensor<i64>
        %74 = tensor.extract %73[] : tensor<i64>
        %75 = arith.cmpi ne, %72, %74 : i64
        %76 = arith.constant false
        %77 = arith.cmpi ne, %75, %76 : i1
        %78 = arith.constant true
        %79 = arith.xori %77, %78 : i1
        %80 = scf.if %79 -> (!jasp.QuantumState) {
          scf.yield %63 : !jasp.QuantumState
        } else {
          %81 = arith.constant 1 : i64
          %82 = arith.subi %56, %81 : i64
          %83 = tensor.from_elements %82 : tensor<i64>
          %84 = jasp.get_qubit %arg116, %83 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %85 = jasp.quantum_gate "x" (%84) , %63 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %85 : !jasp.QuantumState
        }
        %86 = arith.constant 1 : i64
        %87 = arith.subi %56, %86 : i64
        %88 = tensor.from_elements %87 : tensor<i64>
        %89 = jasp.get_qubit %arg116, %88 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %90 = jasp.get_qubit %arg116, %57 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %91 = func.call @jasp_gidney_mcx(%89, %62, %90, %80) : (!jasp.Qubit, !jasp.Qubit, !jasp.Qubit, !jasp.QuantumState) -> !jasp.QuantumState
        %92 = arith.constant true
        %93 = arith.xori %77, %92 : i1
        %94 = scf.if %93 -> (!jasp.QuantumState) {
          scf.yield %91 : !jasp.QuantumState
        } else {
          %95 = arith.constant 1 : i64
          %96 = arith.subi %56, %95 : i64
          %97 = tensor.from_elements %96 : tensor<i64>
          %98 = jasp.get_qubit %arg116, %97 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %99 = jasp.quantum_gate "x" (%98) , %91 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %99 : !jasp.QuantumState
        }
        %100 = arith.constant 1 : i64
        %101 = arith.subi %56, %100 : i64
        %102 = tensor.from_elements %101 : tensor<i64>
        %103 = jasp.get_qubit %arg116, %102 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %104 = jasp.quantum_gate "cx" (%103, %90) , %94 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %105 = arith.constant 1 : i64
        %106 = tensor.extract %arg120[] : tensor<i64>
        %107 = arith.addi %106, %105 : i64
        %108 = tensor.from_elements %107 : tensor<i64>
        %109 = func.call @_jrange_marker(%108, %arg119) : (tensor<i64>, tensor<i64>) -> tensor<i64>
        scf.yield %arg116, %arg117, %arg118, %arg119, %109, %104 : !jasp.QubitArray, !jasp.QubitArray, tensor<i64>, tensor<i64>, tensor<i64>, !jasp.QuantumState
      }
      %110 = arith.constant 2 : i64
      %111 = tensor.extract %3[] : tensor<i64>
      %112 = arith.subi %111, %110 : i64
      %113 = tensor.from_elements %112 : tensor<i64>
      %114 = jasp.get_qubit %14, %113 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %115 = arith.constant 1 : i64
      %116 = tensor.extract %3[] : tensor<i64>
      %117 = arith.subi %116, %115 : i64
      %118 = tensor.from_elements %117 : tensor<i64>
      %119 = jasp.get_qubit %2, %118 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
      %120 = jasp.quantum_gate "cx" (%114, %119) , %50 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %121 = arith.constant 2 : i64
      %122 = tensor.extract %3[] : tensor<i64>
      %123 = arith.subi %122, %121 : i64
      %124 = arith.constant 1 : i64
      %125 = arith.subi %123, %124 : i64
      %126 = tensor.from_elements %125 : tensor<i64>
      %127 = arith.subi %125, %125 : i64
      %128 = tensor.from_elements %127 : tensor<i64>
      %129, %130, %131, %132, %133, %134, %135 = scf.while (%arg95 = %3, %arg96 = %14, %arg97 = %arg20, %arg98 = %2, %arg99 = %126, %arg100 = %128, %arg101 = %120) : (tensor<i64>, !jasp.QubitArray, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (tensor<i64>, !jasp.QubitArray, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
        %136 = tensor.extract %arg100[] : tensor<i64>
        %137 = tensor.extract %arg99[] : tensor<i64>
        %138 = arith.cmpi sle, %136, %137 : i64
        scf.condition(%138) %arg95, %arg96, %arg97, %arg98, %arg99, %arg100, %arg101 : tensor<i64>, !jasp.QubitArray, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
      } do {
      ^bb1(%arg57: tensor<i64>, %arg58: !jasp.QubitArray, %arg59: tensor<i64>, %arg60: !jasp.QubitArray, %arg61: tensor<i64>, %arg62: tensor<i64>, %arg63: !jasp.QuantumState):
        %139 = tensor.extract %arg57[] : tensor<i64>
        %140 = tensor.extract %arg62[] : tensor<i64>
        %141 = arith.subi %139, %140 : i64
        %142 = arith.constant 2 : i64
        %143 = arith.subi %141, %142 : i64
        %144 = tensor.from_elements %143 : tensor<i64>
        %145 = arith.constant 1 : i64
        %146 = arith.subi %143, %145 : i64
        %147 = tensor.from_elements %146 : tensor<i64>
        %148 = jasp.get_qubit %arg58, %147 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %149 = jasp.get_qubit %arg58, %144 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %150 = jasp.quantum_gate "cx" (%148, %149) , %arg63 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        %151 = tensor.extract %arg59[] : tensor<i64>
        %152 = arith.constant 63 : i64
        %153 = arith.shrsi %151, %152 : i64
        %154 = arith.shrsi %151, %143 : i64
        %155 = arith.constant 64 : i64
        %156 = arith.cmpi ugt, %155, %143 : i64
        %157 = arith.select %156, %154, %153 : i64
        %158 = arith.constant 1 : i64
        %159 = arith.andi %157, %158 : i64
        %160 = arith.constant dense<0> : tensor<i64>
        %161 = tensor.extract %160[] : tensor<i64>
        %162 = arith.cmpi ne, %159, %161 : i64
        %163 = arith.constant false
        %164 = arith.cmpi ne, %162, %163 : i1
        %165 = arith.constant true
        %166 = arith.xori %164, %165 : i1
        %167 = scf.if %166 -> (!jasp.QuantumState) {
          scf.yield %150 : !jasp.QuantumState
        } else {
          %168 = arith.constant 1 : i64
          %169 = arith.subi %143, %168 : i64
          %170 = tensor.from_elements %169 : tensor<i64>
          %171 = jasp.get_qubit %arg58, %170 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %172 = jasp.quantum_gate "x" (%171) , %150 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %172 : !jasp.QuantumState
        }
        %173 = arith.constant 1 : i64
        %174 = arith.subi %143, %173 : i64
        %175 = tensor.from_elements %174 : tensor<i64>
        %176 = jasp.get_qubit %arg58, %175 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %177 = jasp.get_qubit %arg60, %144 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %178 = func.call @jasp_gidney_mcx_dg(%176, %177, %149, %167) : (!jasp.Qubit, !jasp.Qubit, !jasp.Qubit, !jasp.QuantumState) -> !jasp.QuantumState
        %179 = arith.constant true
        %180 = arith.xori %164, %179 : i1
        %181 = scf.if %180 -> (!jasp.QuantumState) {
          scf.yield %178 : !jasp.QuantumState
        } else {
          %182 = arith.constant 1 : i64
          %183 = arith.subi %143, %182 : i64
          %184 = tensor.from_elements %183 : tensor<i64>
          %185 = jasp.get_qubit %arg58, %184 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
          %186 = jasp.quantum_gate "x" (%185) , %178 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
          scf.yield %186 : !jasp.QuantumState
        }
        %187 = arith.constant 1 : i64
        %188 = tensor.extract %arg62[] : tensor<i64>
        %189 = arith.addi %188, %187 : i64
        %190 = tensor.from_elements %189 : tensor<i64>
        %191 = func.call @_jrange_marker(%190, %arg61) : (tensor<i64>, tensor<i64>) -> tensor<i64>
        scf.yield %arg57, %arg58, %arg59, %arg60, %arg61, %191, %181 : tensor<i64>, !jasp.QubitArray, tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
      }
      %192 = arith.constant true
      %193 = arith.xori %29, %192 : i1
      %194 = scf.if %193 -> (!jasp.QuantumState) {
        scf.yield %135 : !jasp.QuantumState
      } else {
        %195 = arith.constant dense<0> : tensor<i64>
        %196 = jasp.get_qubit %2, %195 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %197 = jasp.get_qubit %14, %195 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %198 = jasp.quantum_gate "cx" (%196, %197) , %135 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %198 : !jasp.QuantumState
      }
      %199 = jasp.delete_qubits %14, %194 : !jasp.QubitArray, !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %199 : !jasp.QuantumState
    }
    %200 = func.call @tracerizer() : () -> tensor<i64>
    %201 = arith.constant 1 : i64
    %202 = tensor.extract %3[] : tensor<i64>
    %203 = arith.subi %202, %201 : i64
    %204 = tensor.from_elements %203 : tensor<i64>
    %205, %206, %207, %208, %209 = scf.while (%arg45 = %arg20, %arg46 = %2, %arg47 = %204, %arg48 = %200, %arg49 = %9) : (tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) -> (tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState) {
      %210 = tensor.extract %arg48[] : tensor<i64>
      %211 = tensor.extract %arg47[] : tensor<i64>
      %212 = arith.cmpi sle, %210, %211 : i64
      scf.condition(%212) %arg45, %arg46, %arg47, %arg48, %arg49 : tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    } do {
    ^bb2(%arg24: tensor<i64>, %arg25: !jasp.QubitArray, %arg26: tensor<i64>, %arg27: tensor<i64>, %arg28: !jasp.QuantumState):
      %213 = tensor.extract %arg24[] : tensor<i64>
      %214 = tensor.extract %arg27[] : tensor<i64>
      %215 = arith.constant 63 : i64
      %216 = arith.shrsi %213, %215 : i64
      %217 = arith.shrsi %213, %214 : i64
      %218 = arith.constant 64 : i64
      %219 = arith.cmpi ugt, %218, %214 : i64
      %220 = arith.select %219, %217, %216 : i64
      %221 = arith.constant 1 : i64
      %222 = arith.andi %220, %221 : i64
      %223 = arith.constant dense<0> : tensor<i64>
      %224 = tensor.extract %223[] : tensor<i64>
      %225 = arith.cmpi ne, %222, %224 : i64
      %226 = arith.constant false
      %227 = arith.cmpi ne, %225, %226 : i1
      %228 = arith.constant true
      %229 = arith.xori %227, %228 : i1
      %230 = scf.if %229 -> (!jasp.QuantumState) {
        scf.yield %arg28 : !jasp.QuantumState
      } else {
        %231 = jasp.get_qubit %arg25, %arg27 : !jasp.QubitArray, tensor<i64> -> !jasp.Qubit
        %232 = jasp.quantum_gate "x" (%231) , %arg28 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
        scf.yield %232 : !jasp.QuantumState
      }
      %233 = arith.constant 1 : i64
      %234 = tensor.extract %arg27[] : tensor<i64>
      %235 = arith.addi %234, %233 : i64
      %236 = tensor.from_elements %235 : tensor<i64>
      %237 = func.call @_jrange_marker(%236, %arg26) : (tensor<i64>, tensor<i64>) -> tensor<i64>
      scf.yield %arg24, %arg25, %arg26, %237, %230 : tensor<i64>, !jasp.QubitArray, tensor<i64>, tensor<i64>, !jasp.QuantumState
    }
    func.return %209 : !jasp.QuantumState
  }
  func.func private @jasp_gidney_mcx(%arg16: !jasp.Qubit, %arg17: !jasp.Qubit, %arg18: !jasp.Qubit, %arg19: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = func.call @gidney_mcx_impl(%arg16, %arg17, %arg18, %arg19) : (!jasp.Qubit, !jasp.Qubit, !jasp.Qubit, !jasp.QuantumState) -> !jasp.QuantumState
    func.return %0 : !jasp.QuantumState
  }
  func.func private @gidney_mcx_impl(%arg12: !jasp.Qubit, %arg13: !jasp.Qubit, %arg14: !jasp.Qubit, %arg15: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.quantum_gate "h" (%arg14) , %arg15 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %1 = jasp.quantum_gate "t" (%arg14) , %0 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %2 = jasp.quantum_gate "cx" (%arg12, %arg14) , %1 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %3 = jasp.quantum_gate "cx" (%arg13, %arg14) , %2 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %4 = jasp.quantum_gate "cx" (%arg14, %arg12) , %3 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %5 = jasp.quantum_gate "cx" (%arg14, %arg13) , %4 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %6 = jasp.quantum_gate "t_dg" (%arg12) , %5 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %7 = jasp.quantum_gate "t_dg" (%arg13) , %6 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %8 = jasp.quantum_gate "t" (%arg14) , %7 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %9 = jasp.quantum_gate "cx" (%arg14, %arg12) , %8 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %10 = jasp.quantum_gate "cx" (%arg14, %arg13) , %9 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %11 = jasp.quantum_gate "h" (%arg14) , %10 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %12 = jasp.quantum_gate "s" (%arg14) , %11 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    func.return %12 : !jasp.QuantumState
  }
  func.func private @_jrange_marker(%arg10: tensor<i64>, %arg11: tensor<i64>) -> (tensor<i64>) {
    func.return %arg10 : tensor<i64>
  }
  func.func private @jasp_gidney_mcx_dg(%arg6: !jasp.Qubit, %arg7: !jasp.Qubit, %arg8: !jasp.Qubit, %arg9: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = func.call @gidney_mcx_inv_impl(%arg6, %arg7, %arg8, %arg9) : (!jasp.Qubit, !jasp.Qubit, !jasp.Qubit, !jasp.QuantumState) -> !jasp.QuantumState
    func.return %0 : !jasp.QuantumState
  }
  func.func private @gidney_mcx_inv_impl(%arg0: !jasp.Qubit, %arg1: !jasp.Qubit, %arg2: !jasp.Qubit, %arg3: !jasp.QuantumState) -> (!jasp.QuantumState) {
    %0 = jasp.quantum_gate "h" (%arg2) , %arg3 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
    %1, %2 = jasp.measure %arg2, %0 : !jasp.Qubit, !jasp.QuantumState -> tensor<i1>, !jasp.QuantumState
    %3 = tensor.extract %1[] : tensor<i1>
    %4 = arith.constant true
    %5 = arith.xori %3, %4 : i1
    %6 = scf.if %5 -> (!jasp.QuantumState) {
      scf.yield %2 : !jasp.QuantumState
    } else {
      %7 = jasp.quantum_gate "cz" (%arg0, %arg1) , %2 : (!jasp.Qubit, !jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      %8 = jasp.quantum_gate "x" (%arg2) , %7 : (!jasp.Qubit) , !jasp.QuantumState -> !jasp.QuantumState
      scf.yield %8 : !jasp.QuantumState
    }
    func.return %6 : !jasp.QuantumState
  }
  func.func private @tracerizer() -> (tensor<i64>) {
    %0 = arith.constant dense<0> : tensor<i64>
    func.return %0 : tensor<i64>
  }
}
