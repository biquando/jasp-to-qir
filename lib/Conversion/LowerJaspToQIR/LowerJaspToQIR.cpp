#include "JaspToQIR/Conversion/LowerJaspToQIR/LowerJaspToQIR.h"

#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "LowerJaspToQIRInternal.h"
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
namespace lowering = mlir::jasp::internal;

struct LowerJaspToQIRPass final
    : PassWrapper<LowerJaspToQIRPass, OperationPass<ModuleOp>> {
    MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(LowerJaspToQIRPass)

    LowerJaspToQIRPass() = default;
    LowerJaspToQIRPass(const LowerJaspToQIRPass &other) : PassWrapper(other)
    {
        resourceManagement = other.resourceManagement;
        resultBufferSize = other.resultBufferSize;
    }

    StringRef getArgument() const final { return "lower-jasp-to-qir"; }
    StringRef getDescription() const final
    {
        return "Lower typed Jasp operations before standard LLVM conversion";
    }

    Option<std::string> resourceManagement{
        *this,
        "resource-management",
        llvm::cl::desc("QIR resource management mode: static or dynamic"),
        llvm::cl::init("dynamic")};

    Option<int64_t> resultBufferSize{
        *this,
        "result-buffer-size",
        llvm::cl::desc("Number of reusable dynamic result slots"),
        llvm::cl::init(64)};

    void runOnOperation() override
    {
        MLIRContext &context = getContext();
        context.loadDialect<arith::ArithDialect,
                            func::FuncDialect,
                            jasp_ir::JaspDialect,
                            LLVM::LLVMDialect,
                            scf::SCFDialect,
                            tensor::TensorDialect>();

        std::optional<lowering::ResourceManagement> parsedResourceManagement =
            lowering::parseResourceManagement(resourceManagement);
        if (!parsedResourceManagement) {
            getOperation().emitError()
                << "resource-management must be 'static' or 'dynamic'";
            signalPassFailure();
            return;
        }

        if (resultBufferSize <= 0) {
            getOperation().emitError()
                << "result-buffer-size must be greater than zero";
            signalPassFailure();
            return;
        }

        lowering::LowerJaspToQIROptions options{*parsedResourceManagement,
                                           resultBufferSize};
        FailureOr<lowering::LowerJaspToQIRModuleInfo> moduleInfo =
            lowering::prepareLowerJaspToQIRModule(getOperation(), options);
        if (failed(moduleInfo)) {
            signalPassFailure();
            return;
        }

        std::unique_ptr<TypeConverter> converter =
            lowering::createLowerJaspToQIRTypeConverter(context, options);
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
        lowering::populateQubitManagementPatterns(
            *converter, patterns, options, *moduleInfo);
        lowering::populateQubitArrayOperationPatterns(
            *converter, patterns, options);
        lowering::populateQuantumGatePatterns(*converter, patterns);
        lowering::populateMeasurementPatterns(
            *converter, patterns, options, *moduleInfo);
        lowering::populateResetPatterns(*converter, patterns, options);
        lowering::populateScalarizationPatterns(*converter, patterns);

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

std::unique_ptr<mlir::Pass> jasp_to_qir::createLowerJaspToQIRPass()
{
    return std::make_unique<LowerJaspToQIRPass>();
}
