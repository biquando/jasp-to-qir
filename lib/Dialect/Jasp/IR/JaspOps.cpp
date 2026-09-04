#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"

#include "mlir/IR/DialectImplementation.h"

// Keep generated definitions after their MLIR prerequisites.
#include "JaspOpsDialect.cpp.inc"

#define GET_TYPEDEF_CLASSES
#include "JaspOpsTypes.cpp.inc"

#define GET_OP_CLASSES
#include "JaspOps.cpp.inc"

void jasp::JaspDialect::initialize() {
  addTypes<
#define GET_TYPEDEF_LIST
#include "JaspOpsTypes.cpp.inc"
      >();
  addOperations<
#define GET_OP_LIST
#include "JaspOps.cpp.inc"
      >();
}
