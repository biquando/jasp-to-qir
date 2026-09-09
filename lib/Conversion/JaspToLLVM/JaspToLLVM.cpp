#include "JaspToQIR/Conversion/JaspToLLVM/JaspToLLVM.h"
#include <optional>

#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "JaspToLLVMInternal.h"
#include "llvm/Support/CommandLine.h"
#include "mlir/Dialect/Math/IR/Math.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/Func/Transforms/FuncConversions.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/Dialect/SCF/Transforms/Patterns.h"
#include "mlir/Dialect/Tensor/IR/Tensor.h"
#include "mlir/IR/BuiltinDialect.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Transforms/DialectConversion.h"

using namespace mlir;

namespace {

namespace jasp_ir = ::jasp;
using namespace mlir::jasp::internal;

std::optional<ResourceManagement> parseResourceManagement(llvm::StringRef value) {
    if (value == "static") {
        return ResourceManagement::Static;
    }
    if (value == "dynamic") {
        return ResourceManagement::Dynamic;
    }
    return std::nullopt;
}

std::optional<std::set<OutputFormat>> parseOutputFormats(llvm::StringRef value) {
    std::set<llvm::StringRef> formatStrings;
    while (value.contains(',')) {
        auto [s1, s2] = value.split(',');
        formatStrings.insert(s1);
        value = s2;
    }
    formatStrings.insert(value);

    std::set<OutputFormat> formats;
    for (const llvm::StringRef &format : formatStrings) {
        if (format == "bitstring") {
            formats.insert(OutputFormat::Bitstring);
        } else if (format == "integer") {
            formats.insert(OutputFormat::Integer);
        } else {
            return std::nullopt;
        }
    }
    return formats;
}


struct JaspToLLVMPass final
    : PassWrapper<JaspToLLVMPass, OperationPass<ModuleOp>> {
    MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(JaspToLLVMPass)

    JaspToLLVMPass() = default;
    JaspToLLVMPass(const JaspToLLVMPass &other) : PassWrapper(other)
    {
        resourceManagement = other.resourceManagement;
        outputFormats = other.outputFormats;
        resultBufferSize = other.resultBufferSize;
        requireMcmr = other.requireMcmr;
        verbose = other.verbose;
    }

    StringRef getArgument() const final { return "convert-jasp-to-llvm"; }
    StringRef getDescription() const final
    {
        return "Lower typed Jasp operations before standard LLVM conversion";
    }

    Option<std::string> resourceManagement{
        *this,
        "resource-management",
        llvm::cl::desc("QIR resource management mode: static, dynamic"),
        llvm::cl::init("dynamic")};

    Option<std::string> outputFormats{
        *this,
        "output-formats",
        llvm::cl::desc("QIR output formats, comma-separated: bitstring, integer"),
        llvm::cl::init("bitstring,integer")};

    Option<int64_t> resultBufferSize{
        *this,
        "result-buffer-size",
        llvm::cl::desc("Number of reusable dynamic result slots"),
        llvm::cl::init(64)};

    Option<bool> requireMcmr{
        *this,
        "require-mcmr",
        llvm::cl::desc("Reset and restore qubits after measurement"),
        llvm::cl::init(false)};

    Option<bool> verbose{
        *this, "verbose",
        llvm::cl::desc("Record all intermediate measurement results"),
        llvm::cl::init(false)};

    void runOnOperation() override
    {
        MLIRContext &context = getContext();
        context.loadDialect<arith::ArithDialect,
                            func::FuncDialect,
                            jasp_ir::JaspDialect,
                            LLVM::LLVMDialect,
                            scf::SCFDialect,
                            tensor::TensorDialect>();

        std::optional<ResourceManagement> parsedResourceManagement =
            parseResourceManagement(resourceManagement);
        if (!parsedResourceManagement) {
            getOperation().emitError()
                << "resource-management must be 'static' or 'dynamic'";
            signalPassFailure();
            return;
        }

        std::optional<std::set<OutputFormat>> parsedOutputFormats =
            parseOutputFormats(outputFormats);
        if (!parsedOutputFormats) {
            getOperation().emitError()
                << "output-formats must be a comma-separated list of 'bitstring', 'integer'";
            signalPassFailure();
            return;
        }

        if (resultBufferSize <= 0) {
            getOperation().emitError()
                << "result-buffer-size must be greater than zero";
            signalPassFailure();
            return;
        }

        JaspToLLVMOptions options{*parsedResourceManagement,
                                  *parsedOutputFormats,
                                  resultBufferSize,
                                  requireMcmr,
                                  verbose};
        FailureOr<JaspToLLVMModuleInfo> moduleInfo =
            prepareJaspToLLVMModule(getOperation(), options);
        if (failed(moduleInfo)) {
            signalPassFailure();
            return;
        }

        std::unique_ptr<TypeConverter> converter =
            createJaspToLLVMTypeConverter(context, options);
        ConversionTarget target(context);
        target.addLegalDialect<BuiltinDialect, LLVM::LLVMDialect>();
        target.addIllegalDialect<jasp_ir::JaspDialect, tensor::TensorDialect>();
        target.addDynamicallyLegalDialect<math::MathDialect>(
            [&](Operation *operation) {
                return converter->isLegal(operation);
            });
        target.addDynamicallyLegalDialect<arith::ArithDialect>(
            [&](Operation *operation) {
                return converter->isLegal(operation);
            });
        target.addDynamicallyLegalDialect<func::FuncDialect>(
            [&](Operation *operation) {
                return converter->isLegal(operation);
            });
        target.addDynamicallyLegalOp<func::FuncOp>([&](func::FuncOp function) {
            return converter->isSignatureLegal(function.getFunctionType())
                && converter->isLegal(&function.getBody());
        });

        RewritePatternSet patterns(&context);
        populateQubitManagementPatterns(
            *converter, patterns, options, *moduleInfo);
        populateQubitArrayOperationPatterns(
            *converter, patterns, options);
        populateQuantumGatePatterns(*converter, patterns);
        populateMeasurementPatterns(
            *converter, patterns, options, *moduleInfo);
        populateResetPatterns(*converter, patterns, options);
        populateScalarizationPatterns(*converter, patterns);

        populateFunctionOpInterfaceTypeConversionPattern<func::FuncOp>(
            patterns, *converter);
        populateCallOpTypeConversionPattern(patterns, *converter);
        populateReturnOpTypeConversionPattern(patterns, *converter);
        scf::populateSCFStructuralTypeConversionsAndLegality(
            *converter, patterns, target);

        if (failed(applyFullConversion(
                getOperation(), target, std::move(patterns))))
        {
            signalPassFailure();
        }
    }
};

} // namespace

std::unique_ptr<mlir::Pass> jasp_to_qir::createJaspToLLVMPass()
{
    return std::make_unique<JaspToLLVMPass>();
}
