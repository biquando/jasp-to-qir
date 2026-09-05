#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "JaspToLLVMInternal.h"
#include "QIRBuilder.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/Dialect/SCF/IR/SCF.h"

using namespace mlir;

namespace mlir::jasp::internal {

namespace {

namespace jasp_ir = ::jasp;

Value normalizeSliceIndex(ConversionPatternRewriter &rewriter,
                          Location location,
                          Value index,
                          Value size)
{
    QIRBuilder qir(rewriter, location);
    Value zero = qir.constantI64(0);
    Value isNegative = LLVM::ICmpOp::create(
        rewriter, location, LLVM::ICmpPredicate::slt, index, zero);
    Value adjusted = LLVM::SelectOp::create(
        rewriter,
        location,
        isNegative,
        LLVM::AddOp::create(rewriter, location, index, size),
        index);
    Value belowZero = LLVM::ICmpOp::create(
        rewriter, location, LLVM::ICmpPredicate::slt, adjusted, zero);
    Value lowerClamped =
        LLVM::SelectOp::create(rewriter, location, belowZero, zero, adjusted);
    Value aboveSize = LLVM::ICmpOp::create(
        rewriter, location, LLVM::ICmpPredicate::sgt, lowerClamped, size);
    return LLVM::SelectOp::create(
        rewriter, location, aboveSize, size, lowerClamped);
}

struct LowerGetQubit final : OpConversionPattern<jasp_ir::GetQubitOp> {
    LowerGetQubit(TypeConverter &converter,
                  MLIRContext *context,
                  JaspToLLVMOptions options)
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
    JaspToLLVMOptions options;
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

struct LowerSlice final : OpConversionPattern<jasp_ir::SliceOp> {
    LowerSlice(TypeConverter &converter,
               MLIRContext *context,
               JaspToLLVMOptions options)
        : OpConversionPattern(converter, context),
          options(options)
    {}

    LogicalResult
    matchAndRewrite(jasp_ir::SliceOp operation,
                    OpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        Location location = operation.getLoc();
        Value array = adaptor.getQbArray();
        Value base = LLVM::ExtractValueOp::create(
            rewriter, location, array, ArrayRef<int64_t>{0});
        Value size = LLVM::ExtractValueOp::create(
            rewriter, location, array, ArrayRef<int64_t>{1});
        Value start =
            normalizeSliceIndex(rewriter, location, adaptor.getStart(), size);
        Value end =
            normalizeSliceIndex(rewriter, location, adaptor.getEnd(), size);
        QIRBuilder qir(rewriter, location);
        Value zero = qir.constantI64(0);
        Value difference = LLVM::SubOp::create(rewriter, location, end, start);
        Value nonEmpty = LLVM::ICmpOp::create(
            rewriter, location, LLVM::ICmpPredicate::sgt, difference, zero);
        Value length = LLVM::SelectOp::create(
            rewriter, location, nonEmpty, difference, zero);

        Value sliceBase;
        if (options.isDynamic()) {
            sliceBase = qir.pointerAddress(base, start);
        } else {
            sliceBase = LLVM::AddOp::create(rewriter, location, base, start);
        }

        rewriter.replaceOp(
            operation,
            qir.qubitArray(options.resourceManagement, sliceBase, length));
        return success();
    }

  private:
    JaspToLLVMOptions options;
};

struct LowerFuse final : OpConversionPattern<jasp_ir::FuseOp> {
    LowerFuse(TypeConverter &converter,
              MLIRContext *context,
              JaspToLLVMOptions options)
        : OpConversionPattern(converter, context),
          options(options)
    {}

    LogicalResult
    matchAndRewrite(jasp_ir::FuseOp operation,
                    OpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        if (!options.isDynamic()) {
            return rewriter.notifyMatchFailure(
                operation, "fusion requires dynamic resource management");
        }

        Location location = operation.getLoc();
        QIRBuilder qir(rewriter, location);
        Value zero = qir.constantI64(0);
        Value one = qir.constantI64(1);

        auto lengthOf = [&](Value value, Type originalType) -> Value {
            if (isa<jasp_ir::QubitType>(originalType)) {
                return one;
            }
            return LLVM::ExtractValueOp::create(
                rewriter, location, value, ArrayRef<int64_t>{1});
        };

        Value left = adaptor.getOperand1();
        Value right = adaptor.getOperand2();
        Type leftType = operation.getOperand1().getType();
        Type rightType = operation.getOperand2().getType();
        Value leftLength = lengthOf(left, leftType);
        Value rightLength = lengthOf(right, rightType);
        Value total =
            LLVM::AddOp::create(rewriter, location, leftLength, rightLength);
        Value destination = qir.dynamicPointerBuffer(total);

        auto append = [&](Value value, Type originalType, Value offset) {
            if (isa<jasp_ir::QubitType>(originalType)) {
                qir.storePointerElement(value, destination, offset);
                return;
            }

            Value source = LLVM::ExtractValueOp::create(
                rewriter, location, value, ArrayRef<int64_t>{0});
            Value length = LLVM::ExtractValueOp::create(
                rewriter, location, value, ArrayRef<int64_t>{1});
            scf::ForOp::create(rewriter,
                               location,
                               zero,
                               length,
                               one,
                               ValueRange{},
                               [&](OpBuilder &builder,
                                   Location loopLocation,
                                   Value index,
                                   ValueRange) {
                                   QIRBuilder loopQir(builder, loopLocation);
                                   Value qubit =
                                       loopQir.pointerElement(source, index);
                                   Value destinationIndex = LLVM::AddOp::create(
                                       builder, loopLocation, offset, index);
                                   loopQir.storePointerElement(
                                       qubit, destination, destinationIndex);
                                   scf::YieldOp::create(builder, loopLocation);
                               });
        };

        append(left, leftType, zero);
        append(right, rightType, leftLength);
        rewriter.replaceOp(
            operation,
            qir.qubitArray(options.resourceManagement, destination, total));
        return success();
    }

  private:
    JaspToLLVMOptions options;
};

} // namespace

void populateQubitArrayOperationPatterns(TypeConverter &converter,
                                         RewritePatternSet &patterns,
                                         const JaspToLLVMOptions &options)
{
    MLIRContext *context = patterns.getContext();
    patterns.add<LowerGetSize>(converter, context);
    patterns.add<LowerFuse, LowerGetQubit, LowerSlice>(
        converter, context, options);
}

} // namespace mlir::jasp::internal
