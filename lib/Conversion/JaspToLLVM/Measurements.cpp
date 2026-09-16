#include <cassert>

#include "JaspToLLVMInternal.h"
#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "QIRBuilder.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/Dialect/SCF/IR/SCF.h"

using namespace mlir;

namespace mlir::jasp::internal {

namespace {

constexpr llvm::StringLiteral resultBufferGlobalName = "__jasp__result_buffer";

// Used in dynamic mode
void initializeResultBuffer(ModuleOp module,
                            ::jasp::MeasureOp operation,
                            ConversionPatternRewriter &rewriter,
                            Type ptrType,
                            int64_t resultBufferSize)
{
    Location location = operation.getLoc();
    auto main = module.lookupSymbol<func::FuncOp>("main");
    assert(main && "entry point must remain a func.func during conversion");

    // Create the global result pointer
    OpBuilder::InsertionGuard guard(rewriter);
    rewriter.setInsertionPointToStart(module.getBody());
    LLVM::GlobalOp::create(rewriter, location, ptrType, false,
                           LLVM::Linkage::Internal, resultBufferGlobalName,
                           LLVM::ZeroAttr::get(rewriter.getContext()), 8);

    // Allocate the result buffer at entrypoint
    rewriter.setInsertionPointToStart(&main.getBody().front());
    QIRBuilder qir(rewriter, location);
    Value capacity = qir.constantI64(resultBufferSize);
    Value buffer = qir.fixedPointerBuffer(resultBufferSize);
    Value null = LLVM::ZeroOp::create(rewriter, location, ptrType);
    qir.call("__quantum__rt__result_array_allocate", ValueRange{capacity, buffer, null});
    Value address = LLVM::AddressOfOp::create(rewriter, location, ptrType, resultBufferGlobalName);
    LLVM::StoreOp::create(rewriter, location, buffer, address, 8);

    // Release the result buffer at all returns
    main.walk([&](func::ReturnOp returnOp) {
        OpBuilder returnBuilder(returnOp);
        QIRBuilder(returnBuilder, returnOp.getLoc())
            .call("__quantum__rt__result_array_release", ValueRange{capacity, buffer});
    });
}

// Dynamic measurements share one buffer allocated in the entry block.
Value getResultBuffer(::jasp::MeasureOp operation,
                      ConversionPatternRewriter &rewriter,
                      int64_t resultBufferSize)
{
    ModuleOp module = operation->getParentOfType<ModuleOp>();
    Type ptrType = LLVM::LLVMPointerType::get(rewriter.getContext());

    if (!module.lookupSymbol<LLVM::GlobalOp>(resultBufferGlobalName)) {
        initializeResultBuffer(module, operation, rewriter, ptrType, resultBufferSize);
    }

    Value address = LLVM::AddressOfOp::create(
        rewriter, operation.getLoc(), ptrType, resultBufferGlobalName);
    return LLVM::LoadOp::create(rewriter, operation.getLoc(), ptrType, address, 8);
}

void declareMeasurementReset(QIRBuilder &qir, MLIRContext *context)
{
    Type ptrType = LLVM::LLVMPointerType::get(context);
    qir.getOrDeclareFunction("__quantum__qis__mresetz__body", TypeRange{ptrType, ptrType});
    qir.getOrDeclareFunction("__quantum__qis__x__body", ptrType);
}


struct LowerMeasureStaticQubit final : OpConversionPattern<::jasp::MeasureOp> {
    LowerMeasureStaticQubit(TypeConverter &converter, MLIRContext *context,
                            const JaspToLLVMOptions &options,
                            const JaspToLLVMModuleInfo &moduleInfo)
        : OpConversionPattern(converter, context), options(options),
          moduleInfo(moduleInfo)
    {}

    LogicalResult
    matchAndRewrite(::jasp::MeasureOp operation, OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        if (!isa<::jasp::QubitType>(operation.getMeasQ().getType())) {
            return rewriter.notifyMatchFailure(operation, "expected a scalar qubit");
        }

        const MeasurementResultRange *resultRange =
            moduleInfo.getMeasurementResultRange(operation.getOperation());
        if (!resultRange) {
            return rewriter.notifyMatchFailure(operation, "missing measurement result plan");
        }

        Value qubit = adaptor.getMeasQ().front();
        QIRBuilder qir(rewriter, operation.getLoc());

        Value bit = qir.measureStaticQubit(qubit, resultRange->base, options.verbose, options.requireMcmr);
        if (options.requireMcmr) {
            declareMeasurementReset(qir, rewriter.getContext());
            qir.restoreMeasuredQubit(qubit, bit);
        }
        rewriter.replaceOp(operation, bit);
        return success();
    }

  private:
    const JaspToLLVMOptions &options;
    const JaspToLLVMModuleInfo &moduleInfo;
};

struct LowerMeasureStaticArray final : OpConversionPattern<::jasp::MeasureOp> {
    LowerMeasureStaticArray(TypeConverter &converter, MLIRContext *context,
                            const JaspToLLVMOptions &options,
                            const JaspToLLVMModuleInfo &moduleInfo)
        : OpConversionPattern(converter, context), options(options),
          moduleInfo(moduleInfo)
    {}

    LogicalResult
    matchAndRewrite(::jasp::MeasureOp operation, OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        if (!isa<::jasp::QubitArrayType>(operation.getMeasQ().getType())) {
            return rewriter.notifyMatchFailure(operation, "expected a qubit array");
        }

        const MeasurementResultRange *resultRange =
            moduleInfo.getMeasurementResultRange(operation.getOperation());
        if (!resultRange) {
            return rewriter.notifyMatchFailure(operation, "missing measurement result plan");
        }

        Value qubits = adaptor.getMeasQ().front();
        QIRBuilder qir(rewriter, operation.getLoc());
        if (options.requireMcmr) {
            declareMeasurementReset(qir, rewriter.getContext());
        }

        Value base = LLVM::ExtractValueOp::create(rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{0});
        Type ptrType = LLVM::LLVMPointerType::get(rewriter.getContext());
        int64_t count = resultRange->count;
        Value packed = qir.constantI64(0);
        for (int64_t index = 0; index < count; ++index) {
            Value offset = qir.constantI64(index);
            Value id = LLVM::AddOp::create(rewriter, operation.getLoc(), base, offset);
            Value qubit = LLVM::IntToPtrOp::create(rewriter, operation.getLoc(), ptrType, id);
            Value bit = qir.measureStaticQubit(qubit, resultRange->base + index, options.verbose, options.requireMcmr);
            if (options.requireMcmr) {
                qir.restoreMeasuredQubit(qubit, bit);
            }
            Value extended = LLVM::ZExtOp::create(rewriter, operation.getLoc(), rewriter.getI64Type(), bit);
            Value shifted = LLVM::ShlOp::create(rewriter, operation.getLoc(), extended, offset);
            packed = LLVM::OrOp::create(rewriter, operation.getLoc(), packed, shifted);
        }
        rewriter.replaceOp(operation, packed);
        return success();
    }

  private:
    const JaspToLLVMOptions &options;
    const JaspToLLVMModuleInfo &moduleInfo;
};

struct LowerMeasureDynamicQubit final : OpConversionPattern<::jasp::MeasureOp> {
    LowerMeasureDynamicQubit(TypeConverter &converter, MLIRContext *context,
                             const JaspToLLVMOptions &options,
                             const JaspToLLVMModuleInfo &moduleInfo)
        : OpConversionPattern(converter, context), options(options),
          moduleInfo(moduleInfo)
    {}

    LogicalResult
    matchAndRewrite(::jasp::MeasureOp operation, OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        if (!isa<::jasp::QubitType>(operation.getMeasQ().getType())) {
            return rewriter.notifyMatchFailure(operation, "expected a scalar qubit");
        }

        const MeasurementResultRange *resultRange =
            moduleInfo.getMeasurementResultRange(operation.getOperation());
        if (!resultRange) {
            return rewriter.notifyMatchFailure(operation, "missing measurement result plan");
        }

        Value qubit = adaptor.getMeasQ().front();
        QIRBuilder qir(rewriter, operation.getLoc());
        if (options.requireMcmr) {
            declareMeasurementReset(qir, rewriter.getContext());
        }

        Value resultBuffer = getResultBuffer(operation, rewriter, options.resultBufferSize);
        Value result = qir.pointerElement(resultBuffer, qir.constantI64(0));
        if (options.requireMcmr) {
            qir.call("__quantum__qis__mresetz__body", ValueRange{qubit, result});
        } else {
            qir.call("__quantum__qis__mz__body", ValueRange{qubit, result});
        }
        if (options.verbose) {
            qir.recordResult(result, resultRange->base);
        }
        Value bit = qir.call("__quantum__rt__read_result",
                        ValueRange{result}, TypeRange{rewriter.getI1Type()})
                    .getResult();
        if (options.requireMcmr) {
            qir.restoreMeasuredQubit(qubit, bit);
        }
        rewriter.replaceOp(operation, bit);
        return success();
    }

  private:
    const JaspToLLVMOptions &options;
    const JaspToLLVMModuleInfo &moduleInfo;
};

struct LowerMeasureDynamicArray final : OpConversionPattern<::jasp::MeasureOp> {
    LowerMeasureDynamicArray(TypeConverter &converter, MLIRContext *context,
                             const JaspToLLVMOptions &options,
                             const JaspToLLVMModuleInfo &moduleInfo)
        : OpConversionPattern(converter, context), options(options),
          moduleInfo(moduleInfo)
    {}

    LogicalResult
    matchAndRewrite(::jasp::MeasureOp operation, OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        if (!isa<::jasp::QubitArrayType>(operation.getMeasQ().getType())) {
            return rewriter.notifyMatchFailure(operation, "expected a qubit array");
        }

        const MeasurementResultRange *resultRange =
            moduleInfo.getMeasurementResultRange(operation.getOperation());
        if (!resultRange) {
            return rewriter.notifyMatchFailure(operation, "missing measurement result plan");
        }

        Value qubits = adaptor.getMeasQ().front();
        QIRBuilder qir(rewriter, operation.getLoc());
        if (options.requireMcmr) {
            declareMeasurementReset(qir, rewriter.getContext());
        }

        Value base = LLVM::ExtractValueOp::create(rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{0});
        Type ptrType = LLVM::LLVMPointerType::get(rewriter.getContext());
        Value size = LLVM::ExtractValueOp::create(rewriter, operation.getLoc(), qubits, ArrayRef<int64_t>{1});
        Value resultBuffer = getResultBuffer(operation, rewriter, options.resultBufferSize);
        Value zero = qir.constantI64(0);
        Value one = qir.constantI64(1);

        // TODO: Runtime error when size exceeds options.resultBufferSize or 64,
        // since the reusable buffer and packed i64 are statically bounded.
        StringRef measureFunction = options.requireMcmr
                                        ? "__quantum__qis__mresetz__body"
                                        : "__quantum__qis__mz__body";
        qir.getOrDeclareFunction(measureFunction, TypeRange{ptrType, ptrType});
        qir.getOrDeclareFunction("__quantum__rt__read_result",
                                 TypeRange{ptrType}, TypeRange{rewriter.getI1Type()});
        scf::ForOp loop = scf::ForOp::create(rewriter, operation.getLoc(), zero, size, one, ValueRange{zero},
            [&](OpBuilder &builder, Location location, Value index, ValueRange accumulators) {
                QIRBuilder loopQir(builder, location);
                Value qubit = loopQir.pointerElement(base, index);
                Value result = loopQir.pointerElement(resultBuffer, index);
                loopQir.callDeclared(measureFunction, ValueRange{qubit, result});
                Value bit = loopQir
                            .callDeclared("__quantum__rt__read_result", result, TypeRange{builder.getI1Type()})
                            .getResult();
                if (options.requireMcmr) {
                    loopQir.restoreMeasuredQubit(qubit, bit);
                }
                Value extended = LLVM::ZExtOp::create(builder, location, builder.getI64Type(), bit);
                Value shifted = LLVM::ShlOp::create(builder, location, extended, index);
                Value packed = LLVM::OrOp::create(builder, location, accumulators.front(), shifted);
                scf::YieldOp::create(builder, location, packed);
            });

        Value packed = loop.getResult(0);
        Value capacity = qir.constantI64(options.resultBufferSize);

        const auto &formats = options.outputFormats;
        if (options.verbose &&
            formats.find(OutputFormat::Bitstring) != formats.end()) {
            qir.call("__quantum__rt__result_array_record_output",
                     ValueRange{capacity, resultBuffer, qir.outputLabel(resultRange->base)});
        }
        if (options.verbose &&
            formats.find(OutputFormat::Integer) != formats.end()) {
            qir.call("__quantum__rt__int_record_output",
                     ValueRange{packed, qir.outputLabel(resultRange->base)});
        }
        rewriter.replaceOp(operation, packed);
        return success();
    }

  private:
    const JaspToLLVMOptions &options;
    const JaspToLLVMModuleInfo &moduleInfo;
};

} // namespace

void populateMeasurementPatterns(TypeConverter &converter,
                                 RewritePatternSet &patterns,
                                 const JaspToLLVMOptions &options,
                                 const JaspToLLVMModuleInfo &moduleInfo)
{
    if (options.isDynamic()) {
        patterns.add<LowerMeasureDynamicQubit, LowerMeasureDynamicArray>(
            converter, patterns.getContext(), options, moduleInfo);
    } else {
        patterns.add<LowerMeasureStaticQubit, LowerMeasureStaticArray>(
            converter, patterns.getContext(), options, moduleInfo);
    }
}

} // namespace mlir::jasp::internal
