#pragma once

#include "mlir/Pass/Pass.h"

namespace jasp_to_qir {

std::unique_ptr<mlir::Pass> createJaspToLLVMPass();

} // namespace jasp_to_qir
