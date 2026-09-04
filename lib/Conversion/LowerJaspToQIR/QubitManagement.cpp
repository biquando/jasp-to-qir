#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "LowerJaspToQIRInternal.h"
#include "QIRBuilder.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/Dialect/SCF/IR/SCF.h"

using namespace mlir;

namespace mlir::jasp::internal {

namespace {

namespace jasp_ir = ::jasp;

struct LowerCreateQuantumKernel final
    : OpConversionPattern<jasp_ir::CreateQuantumKernelOp> {
    using OpConversionPattern::OpConversionPattern;

    LogicalResult
    matchAndRewrite(jasp_ir::CreateQuantumKernelOp operation,
                    OpAdaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        rewriter.eraseOp(operation);
        return success();
    }
};

struct LowerConsumeQuantumKernel final
    : OpConversionPattern<jasp_ir::ConsumeQuantumKernelOp> {
    using OpConversionPattern::OpConversionPattern;

    LogicalResult
    matchAndRewrite(jasp_ir::ConsumeQuantumKernelOp operation,
                    OneToNOpAdaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        rewriter.replaceOpWithNewOp<arith::ConstantOp>(
            operation, rewriter.getBoolAttr(true));
        return success();
    }
};

struct LowerCreateQubits final : OpConversionPattern<jasp_ir::CreateQubitsOp> {
    LowerCreateQubits(TypeConverter &converter,
                      MLIRContext *context,
                      LowerJaspToQIROptions options,
                      const LowerJaspToQIRModuleInfo &moduleInfo)
        : OpConversionPattern(converter, context),
          options(options),
          moduleInfo(moduleInfo)
    {}

    LogicalResult
    matchAndRewrite(jasp_ir::CreateQubitsOp operation,
                    OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        Value size = adaptor.getAmount().front();
        Value base;
        QIRBuilder qir(rewriter, operation.getLoc());

        if (options.resourceManagement == ResourceManagement::Dynamic) {
            Type pointerType =
                LLVM::LLVMPointerType::get(rewriter.getContext());
            // TODO: Reject negative or unreasonably large runtime sizes before
            // using them as an alloca element count.
            base = qir.dynamicPointerBuffer(size);
            Value null =
                LLVM::ZeroOp::create(rewriter, operation.getLoc(), pointerType);
            qir.getOrDeclareFunction("__quantum__rt__qubit_allocate",
                                     TypeRange{pointerType},
                                     TypeRange{pointerType});
            Value zero = qir.constantI64(0);
            Value one = qir.constantI64(1);
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
                    Value qubit =
                        loopQir
                            .callDeclared("__quantum__rt__qubit_allocate",
                                          null,
                                          TypeRange{pointerType})
                            .getResult();
                    loopQir.storePointerElement(qubit, base, index);
                    scf::YieldOp::create(builder, location);
                });
        } else {
            const QubitArrayInfo *allocation =
                moduleInfo.getQubitAllocation(operation.getOperation());
            if (!allocation) {
                return rewriter.notifyMatchFailure(
                    operation, "missing static qubit allocation plan");
            }
            base = qir.constantI64(allocation->base);
        }

        rewriter.replaceOp(
            operation, qir.qubitArray(options.resourceManagement, base, size));
        return success();
    }

  private:
    LowerJaspToQIROptions options;
    const LowerJaspToQIRModuleInfo &moduleInfo;
};

struct LowerDeleteQubits final : OpConversionPattern<jasp_ir::DeleteQubitsOp> {
    LowerDeleteQubits(TypeConverter &converter,
                      MLIRContext *context,
                      LowerJaspToQIROptions options)
        : OpConversionPattern(converter, context),
          options(options)
    {}

    LogicalResult
    matchAndRewrite(jasp_ir::DeleteQubitsOp operation,
                    OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        if (options.resourceManagement == ResourceManagement::Dynamic) {
            Value buffer =
                LLVM::ExtractValueOp::create(rewriter,
                                             operation.getLoc(),
                                             adaptor.getQubits().front(),
                                             ArrayRef<int64_t>{0});
            Value size =
                LLVM::ExtractValueOp::create(rewriter,
                                             operation.getLoc(),
                                             adaptor.getQubits().front(),
                                             ArrayRef<int64_t>{1});
            QIRBuilder qir(rewriter, operation.getLoc());
            Type pointerType =
                LLVM::LLVMPointerType::get(rewriter.getContext());
            qir.getOrDeclareFunction("__quantum__rt__qubit_release",
                                     TypeRange{pointerType});
            Value zero = qir.constantI64(0);
            Value one = qir.constantI64(1);
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
                    Value qubit = loopQir.pointerElement(buffer, index);
                    loopQir.callDeclared("__quantum__rt__qubit_release", qubit);
                    scf::YieldOp::create(builder, location);
                });
        }
        rewriter.eraseOp(operation);
        return success();
    }

  private:
    LowerJaspToQIROptions options;
};

} // namespace

void populateQubitManagementPatterns(TypeConverter &converter,
                                     RewritePatternSet &patterns,
                                     const LowerJaspToQIROptions &options,
                                     const LowerJaspToQIRModuleInfo &moduleInfo)
{
    MLIRContext *context = patterns.getContext();
    patterns.add<LowerCreateQuantumKernel, LowerConsumeQuantumKernel>(converter,
                                                                      context);
    patterns.add<LowerCreateQubits>(converter, context, options, moduleInfo);
    patterns.add<LowerDeleteQubits>(converter, context, options);
}

} // namespace mlir::jasp::internal
