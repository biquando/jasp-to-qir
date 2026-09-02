#include <cassert>

#include "Jasp/IR/JaspOps.h"
#include "JaspToQIRInternal.h"
#include "QIRBuilder.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/Dialect/SCF/IR/SCF.h"

using namespace mlir;

namespace mlir::jasp::detail {

namespace {

constexpr llvm::StringLiteral resultBufferGlobalName = "__jasp__result_buffer";

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
    /// and produces the classical value. Dynamic measurements share one
    /// fixed-size result buffer allocated in the QIR entry block.
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
                Value resultBuffer = getResultBuffer(operation, rewriter);
                Value result =
                    qir.pointerElement(resultBuffer, qir.constantI64(0));
                qir.call("__quantum__qis__mz__body",
                         ValueRange{qubits, result});
                qir.recordResult(result, resultRange->base);
                bit = qir.call("__quantum__rt__read_result",
                               ValueRange{result},
                               TypeRange{rewriter.getI1Type()})
                          .getResult();
            } else {
                bit = qir.measureStaticQubit(qubits, resultRange->base);
            }

            rewriter.replaceOp(operation, bit);
            return success();
        }

        Value base = LLVM::ExtractValueOp::create(
            rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{0});
        Type pointerType = LLVM::LLVMPointerType::get(rewriter.getContext());

        if (options.resourceManagement == ResourceManagement::Dynamic) {
            Value size = LLVM::ExtractValueOp::create(
                rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{1});
            Value resultBuffer = getResultBuffer(operation, rewriter);
            Value zero = qir.constantI64(0);
            Value one = qir.constantI64(1);

            // TODO: Trap when size exceeds options.resultBufferSize or 64,
            // since the reusable buffer and packed i64 are statically bounded.
            qir.getOrDeclareFunction("__quantum__qis__mz__body",
                                     TypeRange{pointerType, pointerType});
            qir.getOrDeclareFunction("__quantum__rt__read_result",
                                     TypeRange{pointerType},
                                     TypeRange{rewriter.getI1Type()});
            scf::ForOp loop = scf::ForOp::create(
                rewriter,
                operation.getLoc(),
                zero,
                size,
                one,
                ValueRange{zero},
                [&](OpBuilder &builder,
                    Location location,
                    Value index,
                    ValueRange accumulators) {
                    QIRBuilder loopQir(builder, location);
                    Value qubit = loopQir.pointerElement(base, index);
                    Value result = loopQir.pointerElement(resultBuffer, index);
                    loopQir.callDeclared("__quantum__qis__mz__body",
                                         ValueRange{qubit, result});
                    Value bit =
                        loopQir
                            .callDeclared("__quantum__rt__read_result",
                                          result,
                                          TypeRange{builder.getI1Type()})
                            .getResult();
                    Value extended = LLVM::ZExtOp::create(
                        builder, location, builder.getI64Type(), bit);
                    Value shifted =
                        LLVM::ShlOp::create(builder, location, extended, index);
                    Value packed = LLVM::OrOp::create(
                        builder, location, accumulators.front(), shifted);
                    scf::YieldOp::create(builder, location, packed);
                });

            Value packed = loop.getResult(0);
            qir.call("__quantum__rt__int_record_output",
                     ValueRange{packed, qir.outputLabel(resultRange->base)});
            rewriter.replaceOp(operation, packed);
            return success();
        }

        int64_t count = resultRange->count;
        Value packed = qir.constantI64(0);
        for (int64_t index = 0; index < count; ++index) {
            Value offset = qir.constantI64(index);
            Value id =
                LLVM::AddOp::create(rewriter, operation.getLoc(), base, offset);
            Value qubit = LLVM::IntToPtrOp::create(
                rewriter, operation.getLoc(), pointerType, id);
            Value bit =
                qir.measureStaticQubit(qubit, resultRange->base + index);
            Value extended = LLVM::ZExtOp::create(
                rewriter, operation.getLoc(), rewriter.getI64Type(), bit);
            Value shifted = LLVM::ShlOp::create(
                rewriter, operation.getLoc(), extended, offset);
            packed = LLVM::OrOp::create(
                rewriter, operation.getLoc(), packed, shifted);
        }
        rewriter.replaceOp(operation, packed);
        return success();
    }

  private:
    Value getResultBuffer(::jasp::MeasureOp operation,
                          ConversionPatternRewriter &rewriter) const
    {
        ModuleOp module = operation->getParentOfType<ModuleOp>();
        Type pointerType = LLVM::LLVMPointerType::get(rewriter.getContext());

        if (!module.lookupSymbol<LLVM::GlobalOp>(resultBufferGlobalName)) {
            initializeResultBuffer(module, operation, rewriter, pointerType);
        }

        Value address = LLVM::AddressOfOp::create(
            rewriter, operation.getLoc(), pointerType, resultBufferGlobalName);
        return LLVM::LoadOp::create(
            rewriter, operation.getLoc(), pointerType, address, 8);
    }

    void initializeResultBuffer(ModuleOp module,
                                ::jasp::MeasureOp operation,
                                ConversionPatternRewriter &rewriter,
                                Type pointerType) const
    {
        Location location = operation.getLoc();
        auto main = module.lookupSymbol<func::FuncOp>("main");
        assert(main && "entry point must remain a func.func during conversion");

        OpBuilder::InsertionGuard guard(rewriter);
        rewriter.setInsertionPointToStart(module.getBody());
        LLVM::GlobalOp::create(rewriter,
                               location,
                               pointerType,
                               false,
                               LLVM::Linkage::Internal,
                               resultBufferGlobalName,
                               LLVM::ZeroAttr::get(rewriter.getContext()),
                               8);

        rewriter.setInsertionPointToStart(&main.getBody().front());
        QIRBuilder qir(rewriter, location);
        Value capacity = qir.constantI64(options.resultBufferSize);
        Value buffer = qir.fixedPointerBuffer(options.resultBufferSize);
        Value null = LLVM::ZeroOp::create(rewriter, location, pointerType);
        qir.call("__quantum__rt__result_array_allocate",
                 ValueRange{capacity, buffer, null});
        Value address = LLVM::AddressOfOp::create(
            rewriter, location, pointerType, resultBufferGlobalName);
        LLVM::StoreOp::create(rewriter, location, buffer, address, 8);

        main.walk([&](func::ReturnOp returnOp) {
            OpBuilder returnBuilder(returnOp);
            QIRBuilder(returnBuilder, returnOp.getLoc())
                .call("__quantum__rt__result_array_release",
                      ValueRange{capacity, buffer});
        });
    }

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
