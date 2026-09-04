#pragma once

#include "LowerJaspToQIRInternal.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/IR/Builders.h"

namespace mlir::jasp::internal {

/// Small helper for emitting the LLVM-dialect representation of QIR runtime
/// and QIS operations at a particular insertion point and location.
class QIRBuilder {
  public:
    QIRBuilder(OpBuilder &builder, Location location)
        : builder(builder),
          location(location)
    {}

    static LLVM::LLVMStructType getQubitArrayType(MLIRContext *context, ResourceManagement resourceManagement);

    LLVM::LLVMFuncOp getOrDeclareFunction(StringRef name, TypeRange argumentTypes, TypeRange resultTypes = {});
    LLVM::CallOp call(StringRef name, ValueRange arguments, TypeRange resultTypes = {});
    LLVM::CallOp callDeclared(StringRef name, ValueRange arguments, TypeRange resultTypes = {});

    Value constantI64(int64_t value);
    Value qubitArray(ResourceManagement resourceManagement, Value base, Value size);
    Value outputLabel(int64_t index);
    void recordResult(Value result, int64_t outputIndex);
    Value pointerAddress(Value buffer, Value index);
    Value pointerElement(Value buffer, Value index);
    void storePointerElement(Value value, Value buffer, Value index);
    Value fixedPointerBuffer(int64_t count);
    Value dynamicPointerBuffer(Value count);
    Value measureStaticQubit(Value qubit, int64_t resultId);

  private:
    OpBuilder &builder;
    Location location;
};

} // namespace mlir::jasp::internal
