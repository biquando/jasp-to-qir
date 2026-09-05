#include <algorithm>

#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "JaspToLLVMInternal.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/IR/Matchers.h"

using namespace mlir;

namespace mlir::jasp::internal {

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
               jasp_ir::FuseOp,
               jasp_ir::GetQubitOp,
               jasp_ir::GetSizeOp,
               jasp_ir::QuantumGateOp,
               jasp_ir::MeasureOp,
               jasp_ir::ResetOp,
               jasp_ir::SliceOp>(operation);
}

bool isQubitType(Type type)
{
    return isa<jasp_ir::QubitType, jasp_ir::QubitArrayType>(type);
}

int64_t normalizeSliceIndex(int64_t index, int64_t size)
{
    if (index < 0) {
        index += size;
    }
    return std::clamp<int64_t>(index, 0, size);
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
                         const JaspToLLVMOptions &options,
                         const JaspToLLVMModuleInfo &moduleInfo)
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

FailureOr<JaspToLLVMModuleInfo>
prepareJaspToLLVMModule(ModuleOp module, const JaspToLLVMOptions &options)
{
    JaspToLLVMModuleInfo moduleInfo;
    moduleInfo.features.hasBackwardsBranching = options.isDynamic();
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

        if (auto function = dyn_cast<func::FuncOp>(operation)) {
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
                if (!options.isDynamic()) {
                    create.emitError(
                        "static QIR resource management requires a "
                        "compile-time constant qubit count");
                    return WalkResult::interrupt();
                }
            } else {
                int64_t count = numQubitsValue.getSExtValue();
                moduleInfo.qubitArraySizes.try_emplace(create.getResult(),
                                                       count);
                if (!options.isDynamic()) {
                    QubitArrayInfo allocation{moduleInfo.requiredQubits, count};
                    moduleInfo.qubitAllocations.try_emplace(operation,
                                                            allocation);
                    moduleInfo.requiredQubits += count;
                }
            }
        } else if (auto slice = dyn_cast<jasp_ir::SliceOp>(operation)) {
            auto source = moduleInfo.qubitArraySizes.find(slice.getQbArray());
            APInt startValue;
            APInt endValue;
            if (source != moduleInfo.qubitArraySizes.end()
                && matchPattern(slice.getStart(), m_ConstantInt(&startValue))
                && matchPattern(slice.getEnd(), m_ConstantInt(&endValue)))
            {
                int64_t start = normalizeSliceIndex(startValue.getSExtValue(),
                                                    source->second);
                int64_t end = normalizeSliceIndex(endValue.getSExtValue(),
                                                  source->second);
                moduleInfo.qubitArraySizes.try_emplace(
                    slice.getResult(), std::max<int64_t>(end - start, 0));
            }
        } else if (auto fuse = dyn_cast<jasp_ir::FuseOp>(operation)) {
            if (!options.isDynamic()) {
                fuse.emitError(
                    "jasp.fuse requires dynamic resource management");
                return WalkResult::interrupt();
            }

            auto operandSize = [&](Value operand) -> std::optional<int64_t> {
                if (isa<jasp_ir::QubitType>(operand.getType())) {
                    return 1;
                }
                auto iterator = moduleInfo.qubitArraySizes.find(operand);
                if (iterator == moduleInfo.qubitArraySizes.end()) {
                    return std::nullopt;
                }
                return iterator->second;
            };
            std::optional<int64_t> left = operandSize(fuse.getOperand1());
            std::optional<int64_t> right = operandSize(fuse.getOperand2());
            if (left && right) {
                moduleInfo.qubitArraySizes.try_emplace(fuse.getResult(),
                                                       *left + *right);
            }
        } else if (auto measure = dyn_cast<jasp_ir::MeasureOp>(operation)) {
            int64_t count = 1;
            Value measuredValue = measure.getMeasQ();
            if (!options.isDynamic()
                && isa<jasp_ir::QubitArrayType>(measuredValue.getType()))
            {
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
            moduleInfo.requiredResults += options.isDynamic() ? 1 : count;
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

} // namespace mlir::jasp::internal
