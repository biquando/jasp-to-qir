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
               JaspToLLVMOptions options)
        : OpConversionPattern(converter, context),
          options(options)
    {}

    LogicalResult
    matchAndRewrite(::jasp::ResetOp operation,
                    OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        Value qubits = adaptor.getQubits().front();
        QIRBuilder qir(rewriter, operation.getLoc());

        if (isa<LLVM::LLVMPointerType>(qubits.getType())) {
            qir.call("__quantum__qis__reset__body", qubits);
            rewriter.eraseOp(operation);
            return success();
        }

        Value base = LLVM::ExtractValueOp::create(
            rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{0});
        Value size = LLVM::ExtractValueOp::create(
            rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{1});
        Value zero = qir.constantI64(0);
        Value one = qir.constantI64(1);
        Type pointerType = LLVM::LLVMPointerType::get(rewriter.getContext());

        qir.getOrDeclareFunction("__quantum__qis__reset__body",
                                 TypeRange{pointerType});
        scf::ForOp::create(
            rewriter,
            operation.getLoc(),
            zero,
            size,
            one,
            ValueRange{},
            [&](OpBuilder &builder,
                Location location,
                Value index,
                ValueRange) {
                QIRBuilder loopQir(builder, location);
                Value qubit;
                if (options.resourceManagement == ResourceManagement::Dynamic) {
                    qubit = loopQir.pointerElement(base, index);
                } else {
                    Value id =
                        LLVM::AddOp::create(builder, location, base, index);
                    qubit = LLVM::IntToPtrOp::create(
                        builder, location, pointerType, id);
                }

                loopQir.callDeclared("__quantum__qis__reset__body", qubit);
                scf::YieldOp::create(builder, location);
            });

        rewriter.eraseOp(operation);
        return success();
    }

  private:
    JaspToLLVMOptions options;
};

} // namespace

void populateResetPatterns(TypeConverter &converter,
                           RewritePatternSet &patterns,
                           const JaspToLLVMOptions &options)
{
    patterns.add<LowerReset>(converter, patterns.getContext(), options);
}

} // namespace mlir::jasp::internal
