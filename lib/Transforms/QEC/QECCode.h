#pragma once

#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "llvm/ADT/SmallVector.h"
#include "mlir/IR/Builders.h"

#include <memory>

namespace jasp_to_qir::qec {

using HelperResults = mlir::FailureOr<llvm::SmallVector<mlir::Value>>;

class Code {
public:
    virtual ~Code() = default;

    // Use the source op for attributes and types. Build the body using the
    // helper's arguments and return the values for its func.return, or failure
    // if the code does not implement that operation.
    virtual HelperResults emit(jasp::CreateQubitsOp, mlir::OpBuilder &, mlir::ValueRange) const = 0;
    virtual HelperResults emit(jasp::DeleteQubitsOp, mlir::OpBuilder &, mlir::ValueRange) const = 0;
    virtual HelperResults emit(jasp::GetQubitOp, mlir::OpBuilder &, mlir::ValueRange) const = 0;
    virtual HelperResults emit(jasp::GetSizeOp, mlir::OpBuilder &, mlir::ValueRange) const = 0;
    virtual HelperResults emit(jasp::SliceOp, mlir::OpBuilder &, mlir::ValueRange) const = 0;
    virtual HelperResults emit(jasp::FuseOp, mlir::OpBuilder &, mlir::ValueRange) const = 0;
    virtual HelperResults emit(jasp::QuantumGateOp, mlir::OpBuilder &, mlir::ValueRange) const = 0;
    virtual HelperResults emit(jasp::MeasureOp, mlir::OpBuilder &, mlir::ValueRange) const = 0;
    virtual HelperResults emit(jasp::ResetOp, mlir::OpBuilder &, mlir::ValueRange) const = 0;
};

std::unique_ptr<Code> createCode(llvm::StringRef name);

} // namespace jasp_to_qir::qec
