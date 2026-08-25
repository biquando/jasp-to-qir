// This pass runs after the standard Func/SCF/CF/Arith conversions, when the
// module contains only LLVM-dialect program structure. It expresses QIR
// declarations and entry-point behavior in MLIR so `mlir-translate` can emit
// them directly. QIR module flags remain in the Python driver because MLIR's
// module-flag operation cannot preserve all required QIR metadata shapes.

#include "JaspToQIR/JaspToQIR.h"

#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/Pass/Pass.h"

using namespace mlir;

namespace {

/// Returns a QIR declaration with the requested signature, creating it when
/// lowering did not already need it. Existing declarations must match exactly.
FailureOr<LLVM::LLVMFuncOp>
ensureQIRFunction(ModuleOp module, OpBuilder &builder, Location location,
                  StringRef name, Type resultType, TypeRange argumentTypes) {
  auto functionType = LLVM::LLVMFunctionType::get(
      resultType, SmallVector<Type>(argumentTypes.begin(), argumentTypes.end()),
      false);
  if (auto function = module.lookupSymbol<LLVM::LLVMFuncOp>(name)) {
    if (function.getFunctionType() != functionType) {
      function.emitError() << "QIR declaration '" << name
                           << "' has an incompatible signature";
      return failure();
    }
    return function;
  }

  OpBuilder::InsertionGuard guard(builder);
  builder.setInsertionPointToStart(module.getBody());
  return LLVM::LLVMFuncOp::create(builder, location, name, functionType);
}

/// Builds LLVM dialect's representation of unit and key-value attributes.
ArrayAttr buildAttributes(OpBuilder &builder,
                                ArrayRef<StringRef> units,
                                ArrayRef<std::pair<StringRef, StringRef>> pairs) {
  SmallVector<Attribute> attributes;
  for (auto unit : units) {
    attributes.push_back(builder.getStringAttr(unit));
  }
  for (auto [key, val] : pairs) {
    attributes.push_back(builder.getArrayAttr(
      {builder.getStringAttr(key), builder.getStringAttr(val)}
    ));
  }
  return builder.getArrayAttr(attributes);
}

/// Applies a unit attribute to one argument of an LLVM function declaration.
void setArgumentAttribute(OpBuilder &builder, LLVM::LLVMFuncOp function,
                          unsigned index, StringRef name) {
  SmallVector<Attribute> argumentAttributes(
      function.getFunctionType().getParams().size(),
      builder.getDictionaryAttr({}));
  argumentAttributes[index] = builder.getDictionaryAttr(
      {builder.getNamedAttr(name, builder.getUnitAttr())});
  function.setArgAttrsAttr(builder.getArrayAttr(argumentAttributes));
}

/// Reads the resource-management decision made by the Jasp lowering pass.
/// Keeping this as a module attribute lets finalization run after all standard
/// dialect conversions without repeating the resource analysis.
FailureOr<bool> usesDynamicResources(ModuleOp module) {
  auto mode = module->getAttrOfType<StringAttr>("metadata.resource_management");
  if (!mode || (mode.getValue() != "static" && mode.getValue() != "dynamic")) {
    module.emitError("missing or invalid metadata.resource_management attribute");
    return failure();
  }
  return mode.getValue() == "dynamic";
}

/// Validates the lowered main function and attaches the Adaptive Profile entry
/// point attributes. Static mode additionally reports its resource counts.
FailureOr<LLVM::LLVMFuncOp>
configureEntryPoint(ModuleOp module, OpBuilder &builder, bool dynamic) {
  auto main = module.lookupSymbol<LLVM::LLVMFuncOp>("main");
  auto expectedType =
      LLVM::LLVMFunctionType::get(builder.getI64Type(), {}, false);
  if (!main || main.getBody().empty() || main.getFunctionType() != expectedType) {
    module.emitError("expected a defined LLVM @main() -> i64 entry point");
    return failure();
  }

  SmallVector<std::pair<StringRef, StringRef>> attributes{
      {"qir_profiles", "adaptive_profile"},
      {"output_labeling_schema", "labeled"}};
  std::string qubitCount;
  std::string resultCount;
  if (!dynamic) {
    auto qubits  = module->getAttrOfType<IntegerAttr>("entrypoint_attribute.required_num_qubits");
    auto results = module->getAttrOfType<IntegerAttr>("entrypoint_attribute.required_num_results");
    if (!qubits || !results) {
      module.emitError("static QIR requires resource-count attributes");
      return failure();
    }
    qubitCount = std::to_string(qubits.getInt());
    resultCount = std::to_string(results.getInt());
    attributes.push_back({"required_num_qubits", qubitCount});
    attributes.push_back({"required_num_results", resultCount});
  }

  main.setPassthroughAttr(
      buildAttributes(builder, {"entry_point"}, attributes));
  return main;
}

/// Ensures every declaration required by the selected QIR resource model is
/// present and carries its ABI attributes. Dynamic Jasp qubits are always
/// owned by a QubitArray allocation; scalar qubit pointers are borrowed from
/// that array, so scalar qubit allocation/release declarations are not needed.
LogicalResult declareQIRFunctions(ModuleOp module, OpBuilder &builder,
                                  bool dynamic) {
  Location location = module.getLoc();
  MLIRContext *context = builder.getContext();
  Type voidType = LLVM::LLVMVoidType::get(context);
  Type pointerType = LLVM::LLVMPointerType::get(context);
  Type i1 = builder.getI1Type();
  Type i64 = builder.getI64Type();

  auto require = [&](StringRef name, Type result,
                     TypeRange arguments) -> FailureOr<LLVM::LLVMFuncOp> {
    return ensureQIRFunction(module, builder, location, name, result,
                             arguments);
  };

  // Used with static and dynamic
  auto mz                   = require("__quantum__qis__mz__body", voidType, TypeRange{pointerType, pointerType});
  auto reset                = require("__quantum__qis__reset__body", voidType, TypeRange{pointerType});
  auto initialize           = require("__quantum__rt__initialize", voidType, TypeRange{pointerType});
  auto read_result          = require("__quantum__rt__read_result", i1, TypeRange{pointerType});
  auto result_record_output = require("__quantum__rt__result_record_output", voidType, TypeRange{pointerType, pointerType});

  if (failed(mz)
   || failed(reset)
   || failed(initialize)
   || failed(read_result)
   || failed(result_record_output)) {
    return failure();
  }

  (*mz).setPassthroughAttr(buildAttributes(builder, {"irreversible"}, {}));
  setArgumentAttribute(builder, *mz, 1, "llvm.writeonly");
  setArgumentAttribute(builder, *read_result, 0, "llvm.readonly");

  if (!dynamic) {
    return success();
  }

  // Used only with dynamic
  auto qubit_array_allocate       = require("__quantum__rt__qubit_array_allocate", voidType, TypeRange{i64, pointerType, pointerType});
  auto qubit_array_release        = require("__quantum__rt__qubit_array_release", voidType, TypeRange{i64, pointerType});
  auto result_allocate            = require("__quantum__rt__result_allocate", pointerType, TypeRange{pointerType});
  auto result_release             = require("__quantum__rt__result_release", voidType, TypeRange{pointerType});
  auto result_array_allocate      = require("__quantum__rt__result_array_allocate", voidType, TypeRange{i64, pointerType, pointerType});
  auto result_array_release       = require("__quantum__rt__result_array_release", voidType, TypeRange{i64, pointerType});
  auto result_array_record_output = require("__quantum__rt__result_array_record_output", voidType, TypeRange{i64, pointerType, pointerType});

  if (failed(qubit_array_allocate)
   || failed(qubit_array_release)
   || failed(result_allocate)
   || failed(result_release)
   || failed(result_array_allocate)
   || failed(result_array_release)
   || failed(result_array_record_output)) {
    return failure();
  }

  return success();
}

/// Inserts the QIR runtime initialization call before all user instructions.
void instrumentEntryPoint(LLVM::LLVMFuncOp main, OpBuilder &builder) {
  Type pointerType = LLVM::LLVMPointerType::get(builder.getContext());
  builder.setInsertionPointToStart(&main.getBody().front());
  Value null = LLVM::ZeroOp::create(builder, main.getLoc(), pointerType);
  LLVM::CallOp::create(
      builder, main.getLoc(), TypeRange{},
      FlatSymbolRefAttr::get(builder.getContext(),
                             "__quantum__rt__initialize"),
      null);
}

struct FinalizeQIRLLVMPass final
    : PassWrapper<FinalizeQIRLLVMPass, OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(FinalizeQIRLLVMPass)

  StringRef getArgument() const final { return "finalize-qir-llvm"; }
  StringRef getDescription() const final {
    return "Finalize QIR declarations and the LLVM entry point";
  }

  void runOnOperation() override {
    ModuleOp module = getOperation();
    OpBuilder builder(&getContext());

    FailureOr<bool> dynamic = usesDynamicResources(module);
    if (failed(dynamic)) {
      signalPassFailure();
      return;
    }

    FailureOr<LLVM::LLVMFuncOp> main =
        configureEntryPoint(module, builder, *dynamic);
    if (failed(main) || failed(declareQIRFunctions(module, builder, *dynamic))) {
      signalPassFailure();
      return;
    }
    instrumentEntryPoint(*main, builder);
  }
};

} // namespace

std::unique_ptr<Pass> mlir::jasp::createFinalizeQIRLLVMPass() {
  return std::make_unique<FinalizeQIRLLVMPass>();
}
