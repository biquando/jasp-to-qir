// Vendored from eclipse-qrisp/Qrisp at commit
// 8408b32caa64f014228e567e2dbf1849e3b1e009.
// SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-with-classpath-exception

include "mlir/IR/DialectBase.td"
include "mlir/IR/AttrTypeBase.td"

def JaspDialect : Dialect {
  let summary = "A dialect for real-time hybrid quantum computation.";
  let description = [{
    This dialect provides simple data structures that enable expression and
    manipulation of quantum computations.
  }];

  let name = "jasp";
  let cppNamespace = "::jasp";
  let useDefaultTypePrinterParser = 1;
}

class JaspType<string name, string typeMnemonic>
    : TypeDef<JaspDialect, name> {
  let mnemonic = typeMnemonic;
}

def QuantumStateType : JaspType<"QuantumState", "QuantumState"> {
  let summary = "An opaque type describing the quantum state of the machine";
  let description = "This object is passed around the program to capture the computations.";
}

def QubitType : JaspType<"Qubit", "Qubit"> {
  let summary = "A type describing an individual qubit";
  let description = "Qubit objects are semantically identical to integers as they simply index the QuantumState.";
}

def QubitArrayType : JaspType<"QubitArray", "QubitArray"> {
  let summary = "A type describing a dynamically sized collection of Qubits";
  let description = "QubitArrays are semantically equivalent to immutable arrays of integers.";
}
