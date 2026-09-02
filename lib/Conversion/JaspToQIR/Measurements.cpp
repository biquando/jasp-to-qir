#include "Jasp/IR/JaspOps.h"
#include "JaspToQIRInternal.h"
#include "QIRBuilder.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"

using namespace mlir;

namespace mlir::jasp::detail {

namespace {

struct LowerMeasure final : OpConversionPattern<::jasp::MeasureOp> {
    LowerMeasure(TypeConverter &converter,
                 MLIRContext *context,
                 JaspToQIROptions options,
                 const JaspToQIRModuleInfo &moduleInfo)
        : OpConversionPattern(converter, context),
          options(options),
          moduleInfo(moduleInfo)
    {}

    /// Lowers scalar and array measurements, records their output immediately,
    /// produces the classical value, and releases dynamic results on every
    /// function return.
    LogicalResult
    matchAndRewrite(::jasp::MeasureOp operation,
                    OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        const MeasurementResultRange *resultRange =
            moduleInfo.getMeasurementResultRange(operation.getOperation());
        if (!resultRange) {
            return rewriter.notifyMatchFailure(
                operation, "missing measurement result plan");
        }

        Value qubits = adaptor.getMeasQ().front();
        QIRBuilder qir(rewriter, operation.getLoc());

        if (isa<LLVM::LLVMPointerType>(qubits.getType())) {
            Value bit;
            if (options.resourceManagement == ResourceManagement::Dynamic) {
                Type pointerType =
                    LLVM::LLVMPointerType::get(rewriter.getContext());
                Value result;
                {
                    OpBuilder::InsertionGuard guard(rewriter);
                    rewriter.setInsertionPointToStart(
                        QIRBuilder::getFunctionEntry(operation));
                    QIRBuilder entryQir(rewriter, operation.getLoc());
                    Value null = LLVM::ZeroOp::create(
                        rewriter, operation.getLoc(), pointerType);
                    result = entryQir
                                 .call("__quantum__rt__result_allocate",
                                       ValueRange{null},
                                       TypeRange{pointerType})
                                 .getResult();
                }

                qir.call("__quantum__qis__mz__body",
                         ValueRange{qubits, result});
                qir.recordResult(result, resultRange->base);
                bit = qir.call("__quantum__rt__read_result",
                               ValueRange{result},
                               TypeRange{rewriter.getI1Type()})
                          .getResult();
                QIRBuilder::releaseAtFunctionReturns(
                    operation, "__quantum__rt__result_release", result);
            } else {
                bit = qir.measureStaticQubit(qubits, resultRange->base);
            }

            rewriter.replaceOp(operation, bit);
            return success();
        }

        int64_t count = resultRange->count;
        Value base = LLVM::ExtractValueOp::create(
            rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{0});
        Type pointerType = LLVM::LLVMPointerType::get(rewriter.getContext());
        Value resultBuffer;
        Value dynamicCount;

        if (options.resourceManagement == ResourceManagement::Dynamic) {
            {
                OpBuilder::InsertionGuard guard(rewriter);
                rewriter.setInsertionPointToStart(
                    QIRBuilder::getFunctionEntry(operation));
                QIRBuilder entryQir(rewriter, operation.getLoc());
                dynamicCount = entryQir.constantI64(count);
                resultBuffer = entryQir.fixedPointerBuffer(count);
                Value null = LLVM::ZeroOp::create(
                    rewriter, operation.getLoc(), pointerType);
                entryQir.call("__quantum__rt__result_array_allocate",
                              ValueRange{dynamicCount, resultBuffer, null});
            }

            for (int64_t index = 0; index < count; ++index) {
                Value offset = qir.constantI64(index);
                Value qubit = qir.pointerElement(base, offset);
                Value result = qir.pointerElement(resultBuffer, offset);
                qir.call("__quantum__qis__mz__body", ValueRange{qubit, result});
            }

            Value label = qir.outputLabel(resultRange->base);
            qir.call("__quantum__rt__result_array_record_output",
                     ValueRange{dynamicCount, resultBuffer, label});
        }

        Value packed = qir.constantI64(0);
        for (int64_t index = 0; index < count; ++index) {
            Value offset = qir.constantI64(index);
            Value bit;
            if (options.resourceManagement == ResourceManagement::Dynamic) {
                Value result = qir.pointerElement(resultBuffer, offset);
                bit = qir.call("__quantum__rt__read_result",
                               ValueRange{result},
                               TypeRange{rewriter.getI1Type()})
                          .getResult();
            } else {
                Value id = LLVM::AddOp::create(
                    rewriter, operation.getLoc(), base, offset);
                Value qubit = LLVM::IntToPtrOp::create(
                    rewriter, operation.getLoc(), pointerType, id);
                bit = qir.measureStaticQubit(qubit, resultRange->base + index);
            }

            Value extended = LLVM::ZExtOp::create(
                rewriter, operation.getLoc(), rewriter.getI64Type(), bit);
            Value shifted = LLVM::ShlOp::create(
                rewriter, operation.getLoc(), extended, qir.constantI64(index));
            packed = LLVM::OrOp::create(
                rewriter, operation.getLoc(), packed, shifted);
        }

        if (options.resourceManagement == ResourceManagement::Dynamic) {
            QIRBuilder::releaseAtFunctionReturns(
                operation,
                "__quantum__rt__result_array_release",
                ValueRange{dynamicCount, resultBuffer});
        }

        rewriter.replaceOp(operation, packed);
        return success();
    }

  private:
    JaspToQIROptions options;
    const JaspToQIRModuleInfo &moduleInfo;
};

} // namespace

void populateMeasurementPatterns(TypeConverter &converter,
                                 RewritePatternSet &patterns,
                                 const JaspToQIROptions &options,
                                 const JaspToQIRModuleInfo &moduleInfo)
{
    patterns.add<LowerMeasure>(
        converter, patterns.getContext(), options, moduleInfo);
}

} // namespace mlir::jasp::detail
