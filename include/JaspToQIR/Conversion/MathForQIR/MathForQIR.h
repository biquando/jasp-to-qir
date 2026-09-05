#pragma once

#include "mlir/Pass/Pass.h"

namespace jasp_to_qir {

std::unique_ptr<mlir::Pass> createMathForQIRPass();

} // namespace jasp_to_qir
