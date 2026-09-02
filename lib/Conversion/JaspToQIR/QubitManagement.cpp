#include "Jasp/IR/JaspOps.h"
#include "JaspToQIRInternal.h"
#include "QIRBuilder.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"

using namespace mlir;

namespace mlir::jasp::detail {

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
                      JaspToQIROptions options,
                      const JaspToQIRModuleInfo &moduleInfo)
        : OpConversionPattern(converter, context),
          options(options),
          moduleInfo(moduleInfo)
    {}

    LogicalResult
    matchAndRewrite(jasp_ir::CreateQubitsOp operation,
                    OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        const QubitArrayInfo *allocation =
            moduleInfo.getQubitAllocation(operation.getOperation());
        if (!allocation) {
            return rewriter.notifyMatchFailure(operation,
                                               "missing qubit allocation plan");
        }

        auto type = QIRBuilder::getQubitArrayType(rewriter.getContext(),
                                                  options.resourceManagement);
        Value arrayStruct =
            LLVM::UndefOp::create(rewriter, operation.getLoc(), type);
        Value size = adaptor.getAmount().front();
        Value base;
        QIRBuilder qir(rewriter, operation.getLoc());

        if (options.resourceManagement == ResourceManagement::Dynamic) {
            Type pointerType =
                LLVM::LLVMPointerType::get(rewriter.getContext());
            base = qir.fixedPointerBuffer(allocation->count);
            Value null =
                LLVM::ZeroOp::create(rewriter, operation.getLoc(), pointerType);
            qir.call("__quantum__rt__qubit_array_allocate",
                     ValueRange{size, base, null});
        } else {
            base = qir.constantI64(allocation->base);
        }

        arrayStruct = LLVM::InsertValueOp::create(rewriter,
                                                  operation.getLoc(),
                                                  arrayStruct,
                                                  base,
                                                  ArrayRef<int64_t>{0});
        arrayStruct = LLVM::InsertValueOp::create(rewriter,
                                                  operation.getLoc(),
                                                  arrayStruct,
                                                  size,
                                                  ArrayRef<int64_t>{1});

        rewriter.replaceOp(operation, arrayStruct);
        return success();
    }

  private:
    JaspToQIROptions options;
    const JaspToQIRModuleInfo &moduleInfo;
};

struct LowerGetQubit final : OpConversionPattern<jasp_ir::GetQubitOp> {
    LowerGetQubit(TypeConverter &converter,
                  MLIRContext *context,
                  JaspToQIROptions options)
        : OpConversionPattern(converter, context),
          options(options)
    {}

    LogicalResult
    matchAndRewrite(jasp_ir::GetQubitOp operation,
                    OpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        Value base = LLVM::ExtractValueOp::create(rewriter,
                                                  operation.getLoc(),
                                                  adaptor.getQbArray(),
                                                  ArrayRef<int64_t>{0});
        Value offset = adaptor.getPosition();
        QIRBuilder qir(rewriter, operation.getLoc());

        if (options.resourceManagement == ResourceManagement::Dynamic) {
            rewriter.replaceOp(operation, qir.pointerElement(base, offset));
        } else {
            Value qubitId =
                LLVM::AddOp::create(rewriter, operation.getLoc(), base, offset);
            rewriter.replaceOpWithNewOp<LLVM::IntToPtrOp>(
                operation,
                LLVM::LLVMPointerType::get(rewriter.getContext()),
                qubitId);
        }
        return success();
    }

  private:
    JaspToQIROptions options;
};

struct LowerDeleteQubits final : OpConversionPattern<jasp_ir::DeleteQubitsOp> {
    LowerDeleteQubits(TypeConverter &converter,
                      MLIRContext *context,
                      JaspToQIROptions options)
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
            QIRBuilder(rewriter, operation.getLoc())
                .call("__quantum__rt__qubit_array_release",
                      ValueRange{size, buffer});
        }
        rewriter.eraseOp(operation);
        return success();
    }

  private:
    JaspToQIROptions options;
};

struct LowerGetSize final : OpConversionPattern<jasp_ir::GetSizeOp> {
    using OpConversionPattern::OpConversionPattern;

    LogicalResult
    matchAndRewrite(jasp_ir::GetSizeOp operation,
                    OpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        rewriter.replaceOpWithNewOp<LLVM::ExtractValueOp>(
            operation, adaptor.getQbArray(), ArrayRef<int64_t>{1});
        return success();
    }
};

} // namespace

void populateQubitManagementPatterns(TypeConverter &converter,
                                     RewritePatternSet &patterns,
                                     const JaspToQIROptions &options,
                                     const JaspToQIRModuleInfo &moduleInfo)
{
    MLIRContext *context = patterns.getContext();
    patterns
        .add<LowerCreateQuantumKernel, LowerConsumeQuantumKernel, LowerGetSize>(
            converter, context);
    patterns.add<LowerCreateQubits>(converter, context, options, moduleInfo);
    patterns.add<LowerDeleteQubits, LowerGetQubit>(converter, context, options);
}

} // namespace mlir::jasp::detail
