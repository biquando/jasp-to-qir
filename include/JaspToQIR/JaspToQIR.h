#pragma once

#include "mlir/Pass/Pass.h"

namespace mlir {
namespace jasp {

/// Lowers Jasp operations before MLIR's standard SCF, CF, and LLVM passes.
std::unique_ptr<Pass> createJaspToQIRPass();

} // namespace jasp
} // namespace mlir
