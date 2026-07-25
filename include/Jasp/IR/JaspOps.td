// Vendored from eclipse-qrisp/Qrisp at commit
// 8408b32caa64f014228e567e2dbf1849e3b1e009.
// SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-with-classpath-exception

include "mlir/IR/OpBase.td"
include "mlir/IR/BuiltinTypes.td"
include "JaspDialect.td"

class JaspOp<string mnemonic, list<Trait> traits = []> :
    Op<JaspDialect, mnemonic, traits>;

def CreateQubitsOp : JaspOp<"create_qubits"> {
  let summary = "Allocates a QubitArray containing n qubits.";
  let arguments = (ins 0DTensorOf<[I64]>:$amount, QuantumStateType:$qst_in);
  let results = (outs QubitArrayType:$result, QuantumStateType:$qst_out);
  // Qrisp prints the two operand types in this historical order.
  let assemblyFormat = "$amount attr-dict `,` $qst_in `:` type($qst_in) `,` type($amount) `->` type($result) `,` type($qst_out)";
}

def GetQubitOp : JaspOp<"get_qubit"> {
  let summary = "Retrieves a single qubit.";
  let arguments = (ins QubitArrayType:$qb_array, 0DTensorOf<[I64]>:$position);
  let results = (outs QubitType:$result);
  let assemblyFormat = "$qb_array `,` $position attr-dict `:` type($qb_array) `,` type($position) `->` type($result)";
}

def GetSizeOp : JaspOp<"get_size"> {
  let summary = "Gets the size of a QubitArray.";
  let arguments = (ins QubitArrayType:$qb_array);
  let results = (outs 0DTensorOf<[I64]>:$size);
  let assemblyFormat = "$qb_array attr-dict `:` type($qb_array) `->` type($size)";
}

def SliceOp : JaspOp<"slice"> {
  let summary = "Slices a QubitArray.";
  let arguments = (ins QubitArrayType:$qb_array, 0DTensorOf<[I64]>:$start,
                       0DTensorOf<[I64]>:$end);
  let results = (outs QubitArrayType:$result);
  let assemblyFormat = "$qb_array `,` $start `,` $end attr-dict `:` type($qb_array) `,` type($start) `,` type($end) `->` type($result)";
}

def FuseOp : JaspOp<"fuse"> {
  let summary = "Concatenates two qubits or qubit arrays.";
  let arguments = (ins AnyTypeOf<[QubitType, QubitArrayType]>:$operand1,
                       AnyTypeOf<[QubitType, QubitArrayType]>:$operand2);
  let results = (outs QubitArrayType:$result);
  let assemblyFormat = "$operand1 `,` $operand2 attr-dict `:` type($operand1) `,` type($operand2) `->` type($result)";
}

def ResetOp : JaspOp<"reset"> {
  let summary = "Resets qubits to the zero state.";
  let arguments = (ins AnyTypeOf<[QubitType, QubitArrayType]>:$qubits,
                       QuantumStateType:$in_qst);
  let results = (outs QuantumStateType:$out_qst);
  let assemblyFormat = "$qubits `,` $in_qst attr-dict `:` type($qubits) `,` type($in_qst) `->` type($out_qst)";
}

def MeasureOp : JaspOp<"measure"> {
  let summary = "Measures a qubit or qubit array.";
  let arguments = (ins AnyTypeOf<[QubitType, QubitArrayType]>:$meas_q,
                       QuantumStateType:$in_qst);
  let results = (outs AnyTypeOf<[0DTensorOf<[I1]>, 0DTensorOf<[I64]>]>:$meas_res,
                      QuantumStateType:$out_qst);
  let assemblyFormat = "$meas_q `,` $in_qst attr-dict `:` type($meas_q) `,` type($in_qst) `->` type($meas_res) `,` type($out_qst)";
  let hasVerifier = 1;
}

def DeleteQubitsOp : JaspOp<"delete_qubits"> {
  let summary = "Deallocates qubits from a QubitArray.";
  let arguments = (ins QubitArrayType:$qubits, QuantumStateType:$in_qst);
  let results = (outs QuantumStateType:$out_qst);
  let assemblyFormat = "$qubits `,` $in_qst attr-dict `:` type($qubits) `,` type($in_qst) `->` type($out_qst)";
}

def CreateQuantumKernelOp : JaspOp<"create_quantum_kernel"> {
  let summary = "Creates a quantum state from nothing.";
  let arguments = (ins);
  let results = (outs QuantumStateType:$result);
  let assemblyFormat = "attr-dict `->` type($result)";
}

def ConsumeQuantumKernelOp : JaspOp<"consume_quantum_kernel"> {
  let summary = "Consumes a quantum state.";
  let arguments = (ins QuantumStateType:$qst);
  let results = (outs 0DTensorOf<[I1]>:$success);
  let assemblyFormat = "$qst attr-dict `:` type($qst) `->` type($success)";
}

def QuantumGateOp : JaspOp<"quantum_gate"> {
  let summary = "Applies a quantum gate.";
  let arguments = (ins StrAttr:$gate_type,
                       Variadic<AnyTypeOf<[0DTensorOf<[F64]>, QubitType]>>:$gate_operands,
                       QuantumStateType:$in_qst);
  let results = (outs QuantumStateType:$out_qst);
  let assemblyFormat = "$gate_type `(` $gate_operands `)` `,` $in_qst attr-dict `:` `(` type($gate_operands) `)` `,` type($in_qst) `->` type($out_qst)";
}

def ParityOp : JaspOp<"parity"> {
  let summary = "Computes parity of measurement results.";
  let arguments = (ins Variadic<0DTensorOf<[I1]>>:$measurements,
                       I64Attr:$expectation, I64Attr:$observable);
  let results = (outs 0DTensorOf<[I1]>:$result);
  let assemblyFormat = "$measurements attr-dict `:` type($measurements) `->` type($result)";
}
