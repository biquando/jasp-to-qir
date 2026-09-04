#pragma once

#include "mlir/Bytecode/BytecodeOpInterface.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/BuiltinTypes.h"
#include "mlir/IR/Dialect.h"
#include "mlir/IR/OpDefinition.h"
#include "mlir/IR/OpImplementation.h"
#include "mlir/IR/Types.h"
#include "llvm/ADT/TypeSwitch.h"

// Keep generated declarations after their MLIR prerequisites.
#include "JaspOpsDialect.h.inc"

#define GET_TYPEDEF_CLASSES
#include "JaspOpsTypes.h.inc"

#define GET_OP_CLASSES
#include "JaspOps.h.inc"
