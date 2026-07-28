#pragma once

#include "mlir/Pass/Pass.h"

namespace mlir {
namespace jasp {

/// Lowers Jasp operations before MLIR's standard SCF, CF, and LLVM passes.
std::unique_ptr<Pass> createJaspToQIRPass();

/// Adds QIR declarations, entry-point attributes, and initialization after
/// standard conversion has produced an LLVM-dialect module.
std::unique_ptr<Pass> createFinalizeQIRLLVMPass();

} // namespace jasp
} // namespace mlir
