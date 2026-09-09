#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"

#include "mlir/IR/DialectImplementation.h"
#include "mlir/Transforms/InliningUtils.h"

// Keep generated definitions after their MLIR prerequisites.
#include "JaspOpsDialect.cpp.inc"

#define GET_TYPEDEF_CLASSES
#include "JaspOpsTypes.cpp.inc"

#define GET_OP_CLASSES
#include "JaspOps.cpp.inc"

namespace {
struct JaspInlinerInterface : mlir::DialectInlinerInterface {
  using DialectInlinerInterface::DialectInlinerInterface;

  bool isLegalToInline(mlir::Operation *, mlir::Region *, bool,
                       mlir::IRMapping &) const override {
    return true;
  }
};
} // namespace

void jasp::JaspDialect::initialize() {
  addInterfaces<JaspInlinerInterface>();
  addTypes<
#define GET_TYPEDEF_LIST
#include "JaspOpsTypes.cpp.inc"
      >();
  addOperations<
#define GET_OP_LIST
#include "JaspOps.cpp.inc"
      >();
}
