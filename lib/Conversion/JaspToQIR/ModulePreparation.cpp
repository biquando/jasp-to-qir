#include "Jasp/IR/JaspOps.h"
#include "JaspToQIRInternal.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/IR/Matchers.h"

using namespace mlir;

namespace mlir::jasp::detail {

namespace {

namespace jasp_ir = ::jasp;

bool containsFloat(Type type)
{
    if (type.isF64()) {
        return true;
    }
    if (auto tensor = dyn_cast<RankedTensorType>(type)) {
        return tensor.getElementType().isF64();
    }
    return false;
}

bool isSupportedJaspOp(Operation *operation)
{
    return isa<jasp_ir::CreateQuantumKernelOp,
               jasp_ir::ConsumeQuantumKernelOp,
               jasp_ir::CreateQubitsOp,
               jasp_ir::DeleteQubitsOp,
               jasp_ir::GetQubitOp,
               jasp_ir::GetSizeOp,
               jasp_ir::QuantumGateOp,
               jasp_ir::MeasureOp,
               jasp_ir::ResetOp>(operation);
}

LogicalResult prepareMain(ModuleOp module)
{
    auto main = module.lookupSymbol<func::FuncOp>("main");
    if (!main) {
        return module.emitError("expected a @main function");
    }
    if (main.getNumArguments() != 1
        || !isa<jasp_ir::QuantumStateType>(main.getArgument(0).getType()))
    {
        return main.emitError("expected one Jasp state argument on @main");
    }

    OpBuilder builder(main.getContext());
    main.setFunctionType(
        builder.getFunctionType(main.getArgumentTypes(), builder.getI64Type()));

    main.walk([&](func::ReturnOp returnOp) {
        OpBuilder returnBuilder(returnOp);
        Value exit =
            arith::ConstantOp::create(returnBuilder,
                                      returnOp.getLoc(),
                                      returnBuilder.getI64IntegerAttr(0));
        returnOp->setOperands(exit);
    });
    return success();
}

void setModuleAttributes(ModuleOp module,
                         const JaspToQIROptions &options,
                         const JaspToQIRModuleInfo &moduleInfo)
{
    MLIRContext *context = module.getContext();
    Type i64 = IntegerType::get(context, 64);

    module->setAttr(
        "metadata.resource_management",
        StringAttr::get(
            context, stringifyResourceManagement(options.resourceManagement)));

    if (options.resourceManagement == ResourceManagement::Static) {
        module->setAttr("entrypoint_attribute.required_num_qubits",
                        IntegerAttr::get(i64, moduleInfo.requiredQubits));
        module->setAttr("entrypoint_attribute.required_num_results",
                        IntegerAttr::get(i64, moduleInfo.requiredResults));
    } else {
        module->removeAttr("entrypoint_attribute.required_num_qubits");
        module->removeAttr("entrypoint_attribute.required_num_results");
    }

    const QIRModuleFeatures &features = moduleInfo.features;
    module->setAttr("module_flag.ir_functions",
                    BoolAttr::get(context, features.hasIrFunctions));
    module->setAttr("module_flag.backwards_branching",
                    BoolAttr::get(context, features.hasBackwardsBranching));
    module->setAttr(
        "module_flag.multiple_target_branching",
        BoolAttr::get(context, features.hasMultipleTargetBranching));
    module->setAttr("module_flag.multiple_return_points",
                    BoolAttr::get(context, features.hasMultipleReturnPoints));
    module->setAttr("module_flag.float_computations",
                    BoolAttr::get(context, features.hasFloatComputations));
}

} // namespace

std::optional<ResourceManagement> parseResourceManagement(llvm::StringRef value)
{
    if (value == "static") {
        return ResourceManagement::Static;
    }
    if (value == "dynamic") {
        return ResourceManagement::Dynamic;
    }
    return std::nullopt;
}

llvm::StringRef
stringifyResourceManagement(ResourceManagement resourceManagement)
{
    switch (resourceManagement) {
    case ResourceManagement::Static:
        return "static";
    case ResourceManagement::Dynamic:
        return "dynamic";
    }
    llvm_unreachable("unknown resource management mode");
}

FailureOr<JaspToQIRModuleInfo>
prepareJaspToQIRModule(ModuleOp module, const JaspToQIROptions &options)
{
    JaspToQIRModuleInfo moduleInfo;
    int64_t functionCount = 0;
    int64_t mainReturnCount = 0;

    WalkResult analysis = module.walk([&](Operation *operation) {
        moduleInfo.features.hasBackwardsBranching |=
            isa<scf::ForOp, scf::ParallelOp, scf::WhileOp>(operation);
        moduleInfo.features.hasMultipleTargetBranching |=
            isa<scf::IndexSwitchOp>(operation);
        for (Type type : operation->getOperandTypes()) {
            moduleInfo.features.hasFloatComputations |= containsFloat(type);
        }
        for (Type type : operation->getResultTypes()) {
            moduleInfo.features.hasFloatComputations |= containsFloat(type);
        }

        if (isa<func::FuncOp>(operation)) {
            ++functionCount;
        } else if (auto returnOp = dyn_cast<func::ReturnOp>(operation)) {
            if (returnOp->getParentOfType<func::FuncOp>().getSymName()
                == "main")
            {
                ++mainReturnCount;
            }
        } else if (auto create = dyn_cast<jasp_ir::CreateQubitsOp>(operation)) {
            APInt numQubitsValue;
            if (!matchPattern(create.getAmount(),
                              m_ConstantInt(&numQubitsValue)))
            {
                create.emitError(
                    "QIR array backing storage requires a compile-time "
                    "constant size");
                return WalkResult::interrupt();
            }

            int64_t count = numQubitsValue.getSExtValue();
            QubitArrayInfo allocation{moduleInfo.requiredQubits, count};
            moduleInfo.qubitAllocations.try_emplace(operation, allocation);
            moduleInfo.qubitArraySizes.try_emplace(create.getResult(), count);
            moduleInfo.requiredQubits += count;
        } else if (auto measure = dyn_cast<jasp_ir::MeasureOp>(operation)) {
            int64_t count = 1;
            Value measuredValue = measure.getMeasQ();
            if (isa<jasp_ir::QubitArrayType>(measuredValue.getType())) {
                auto iterator = moduleInfo.qubitArraySizes.find(measuredValue);
                if (iterator == moduleInfo.qubitArraySizes.end()) {
                    measure.emitError("Could not statically determine size of "
                                      "measured qubit array");
                    return WalkResult::interrupt();
                }
                count = iterator->second;
            }

            MeasurementResultRange range{moduleInfo.requiredResults, count};
            moduleInfo.measurementResultRanges.try_emplace(operation, range);
            moduleInfo.requiredResults += count;
        } else if (auto gate = dyn_cast<jasp_ir::QuantumGateOp>(operation)) {
            if (!isSupportedQuantumGate(gate.getGateType())) {
                gate.emitError()
                    << "Unsupported Jasp gate '" << gate.getGateType() << "'";
                return WalkResult::interrupt();
            }
        } else if (operation->getDialect()
                   && operation->getDialect()->getNamespace() == "jasp"
                   && !isSupportedJaspOp(operation))
        {
            operation->emitError() << "Unsupported Jasp operation '"
                                   << operation->getName() << "'";
            return WalkResult::interrupt();
        }

        return WalkResult::advance();
    });

    if (analysis.wasInterrupted() || failed(prepareMain(module))) {
        return failure();
    }

    moduleInfo.features.hasIrFunctions = functionCount > 1;
    moduleInfo.features.hasMultipleReturnPoints = mainReturnCount > 1;
    setModuleAttributes(module, options, moduleInfo);
    return moduleInfo;
}

} // namespace mlir::jasp::detail
