#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "JaspToLLVMInternal.h"
#include "QIRBuilder.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/Dialect/SCF/IR/SCF.h"

using namespace mlir;

namespace mlir::jasp::internal {

namespace {

struct LowerReset final : OpConversionPattern<::jasp::ResetOp> {
    LowerReset(TypeConverter &converter,
               MLIRContext *context,
               JaspToLLVMOptions options,
               const JaspToLLVMModuleInfo &moduleInfo)
        : OpConversionPattern(converter, context),
          options(options), moduleInfo(moduleInfo)
    {}

    LogicalResult
    matchAndRewrite(::jasp::ResetOp operation,
                    OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        Value qubits = adaptor.getQubits().front();
        QIRBuilder qir(rewriter, operation.getLoc());
        Type ptrType = LLVM::LLVMPointerType::get(rewriter.getContext());
        qir.getOrDeclareFunction("__quantum__qis__reset__body", TypeRange{ptrType});

        // Single qubit reset
        if (isa<LLVM::LLVMPointerType>(qubits.getType())) {
            qir.call("__quantum__qis__reset__body", qubits);
            rewriter.eraseOp(operation);
            return success();
        }

        Value base = LLVM::ExtractValueOp::create(
            rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{0});

        // Static array reset
        if (options.resourceManagement == ResourceManagement::Static) {
            auto size = moduleInfo.qubitArraySizes.find(operation.getQubits());
            if (size == moduleInfo.qubitArraySizes.end()) {
                return operation.emitError(
                    "static array reset requires a compile-time constant qubit count");
            }
            for (int64_t index = 0; index < size->second; ++index) {
                Value id = LLVM::AddOp::create(
                    rewriter, operation.getLoc(), base, qir.constantI64(index));
                Value qubit = LLVM::IntToPtrOp::create(
                    rewriter, operation.getLoc(), ptrType, id);
                qir.call("__quantum__qis__reset__body", qubit);
            }
            rewriter.eraseOp(operation);
            return success();
        }

        // Dynamic array reset
        Value size = LLVM::ExtractValueOp::create(
            rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{1});
        Value zero = qir.constantI64(0);
        Value one = qir.constantI64(1);
        // for (i = 0; i < size; i++) { reset(qubits[i]) }
        scf::ForOp::create(rewriter, operation.getLoc(), zero, size, one, ValueRange{},
            [&](OpBuilder &builder, Location location, Value index, ValueRange) {
                QIRBuilder loopQir(builder, location);
                Value qubit = loopQir.pointerElement(base, index);
                loopQir.callDeclared("__quantum__qis__reset__body", qubit);
                scf::YieldOp::create(builder, location);
            });

        rewriter.eraseOp(operation);
        return success();
    }

  private:
    JaspToLLVMOptions options;
    const JaspToLLVMModuleInfo &moduleInfo;
};

} // namespace

void populateResetPatterns(TypeConverter &converter,
                           RewritePatternSet &patterns,
                           const JaspToLLVMOptions &options,
                           const JaspToLLVMModuleInfo &moduleInfo)
{
    patterns.add<LowerReset>(converter, patterns.getContext(), options, moduleInfo);
}

} // namespace mlir::jasp::internal
