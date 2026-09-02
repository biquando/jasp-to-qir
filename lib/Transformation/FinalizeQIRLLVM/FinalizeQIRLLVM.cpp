#include "JaspToQIR/JaspToQIR.h"

#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/Pass/Pass.h"

using namespace mlir;

namespace {

/// Replace the temporary global result-buffer alias after inlining. This leaves
/// every measurement using the entry block's stack allocation directly, as
/// required by the QIR validator.
constexpr llvm::StringLiteral resultBufferGlobalName = "__jasp__result_buffer";
LogicalResult useDirectResultBuffer(ModuleOp &module) {
  auto global = module.lookupSymbol<LLVM::GlobalOp>(resultBufferGlobalName);
  if (!global) {
    return success();
  }

  auto main = module.lookupSymbol<LLVM::LLVMFuncOp>("main");
  if (!main || main.getBody().empty()) {
    return module.emitError("expected an LLVM @main entry point");
  }

  // Find all uses of the global alias
  SmallVector<LLVM::AddressOfOp> addresses;
  module.walk([&](LLVM::AddressOfOp address) {
    if (address.getGlobalName() == resultBufferGlobalName) {
      addresses.push_back(address);
    }
  });

  // Find the stack-allocated buffer that gets stored into the global alias.
  // If multiple buffers get stored into the global, they must be identical.
  Value buffer;
  for (LLVM::AddressOfOp address : addresses) {
    for (Operation *user : address->getUsers()) {
      auto store = dyn_cast<LLVM::StoreOp>(user);
      if (!store || store.getAddr() != address.getResult()) {
        continue;
      }
      if (buffer && buffer != store.getValue()) {
        return store.emitError("conflicting result buffer aliases");
      }
      buffer = store.getValue();
    }
  }
  if (!buffer) {
    return global.emitError("missing result buffer initialization");
  }
  auto allocation = buffer.getDefiningOp<LLVM::AllocaOp>();
  if (!allocation || allocation->getBlock() != &main.getBody().front()) {
    return global.emitError(
        "result buffer must be stack-allocated in the entry block");
  }

  // Replace each use of the global alias with the original stack-allocated
  // result buffer.
  for (LLVM::AddressOfOp address : addresses) {
    SmallVector<Operation *> users(address->getUsers());
    for (Operation *user : users) {
      if (auto load = dyn_cast<LLVM::LoadOp>(user)) {
        if (load->getParentOfType<LLVM::LLVMFuncOp>() != main) {
          return load.emitError(
              "result buffer user remained outside @main after inlining");
        }
        load.getResult().replaceAllUsesWith(buffer);
        load.erase();
      } else if (auto store = dyn_cast<LLVM::StoreOp>(user)) {
        if (store.getAddr() != address.getResult()
            || store.getValue() != buffer) {
          return store.emitError("unexpected result buffer alias store");
        }
        store.erase();
      } else {
        return user->emitError("unexpected use of result buffer alias");
      }
    }
    address.erase();
  }
  global.erase();
  return success();
}

/// Gets the resource management mode ("static" or "dynamic") from the module
/// metadata attribute.
FailureOr<StringRef> resourceManagementMode(ModuleOp &module) {
  auto attr = module->getAttrOfType<StringAttr>("metadata.resource_management");
  if (!attr || attr.getValue() != "static" && attr.getValue() != "dynamic") {
    module.emitError("missing or invalid resource management mode");
    return failure();
  }
  return attr.getValue();
}

/// Constructs some unit and key-value attributes.
ArrayAttr buildAttributes(OpBuilder &builder,
                          ArrayRef<StringRef> unitAttrs,
                          ArrayRef<std::pair<StringRef, StringRef>> kvAttrs) {
  SmallVector<Attribute> attrs;
  for (auto unitAttr : unitAttrs) {
    attrs.push_back(builder.getStringAttr(unitAttr));
  }
  for (auto [key, val] : kvAttrs) {
    attrs.push_back(builder.getArrayAttr(
      { builder.getStringAttr(key), builder.getStringAttr(val) }
    ));
  }
  return builder.getArrayAttr(attrs);
}

/// Adds the required attributes to the llvm entrypoint function:
///  - "entrypoint"
///  - "qir_profiles"="adaptive_profile"
///  - "output_labeling_schema"="labeled"
/// If static resource allocation is used, we also need:
///  - "required_num_qubits"=...
///  - "required_num_results"=...
LogicalResult addEntrypointAttributes(ModuleOp &module, OpBuilder &builder, StringRef mode) {
  auto main = module.lookupSymbol<LLVM::LLVMFuncOp>("main");
  auto expectedType = LLVM::LLVMFunctionType::get(builder.getI64Type(), {}, false);
  if (!main || main.getBody().empty() || main.getFunctionType() != expectedType) {
    module.emitError("expected an LLVM @main() -> i64 entry point");
    return failure();
  }

  SmallVector<std::pair<StringRef, StringRef>> attributes{
      {"qir_profiles", "adaptive_profile"},
      {"output_labeling_schema", "labeled"}};

  std::string qubitCount;
  std::string resultCount;
  if (mode == "static") {
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

  main.setPassthroughAttr(buildAttributes(builder, {"entry_point"}, attributes));
  return success();
}

/// Add attributes to QIR function declarations.
LogicalResult addDeclarationAttributes(ModuleOp &module, OpBuilder &builder) {
  // Measurements should be irreversible, and the result arguments should be writeonly.
  auto mz = module.lookupSymbol<LLVM::LLVMFuncOp>("__quantum__qis__mz__body");
  if (mz) {
    if (mz.getNumArguments() != 2) {
      mz.emitError("expected mz to have two arguments");
      return failure();
    }
    mz.setPassthroughAttr(buildAttributes(builder, {"irreversible"}, {}));
    mz.setArgAttrs(1, builder.getNamedAttr("llvm.writeonly", builder.getUnitAttr()));
  }

  // Read result's argument should be annotated as readonly.
  auto readResult = module.lookupSymbol<LLVM::LLVMFuncOp>("__quantum__rt__read_result");
  if (readResult) {
    if (readResult.getNumArguments() != 1) {
      readResult.emitError("expected read_result to have one argument");
      return failure();
    }
    readResult.setArgAttrs(0, builder.getNamedAttr("llvm.readonly", builder.getUnitAttr()));
  }

  return success();
}

/// Add call to __quantum__rt__initialize at the module's entrypoint.
LogicalResult instrumentEntryPoint(ModuleOp &module, OpBuilder &builder) {
  // Declare __quantum__rt__initialize
  if (!module.lookupSymbol<LLVM::LLVMFuncOp>("__quantum__rt__initialize")) {
    builder.setInsertionPointToStart(module.getBody());
    auto context = builder.getContext();
    Type voidType = LLVM::LLVMVoidType::get(context);
    Type ptrType = LLVM::LLVMPointerType::get(context);
    LLVM::LLVMFuncOp::create(builder, module.getLoc(), "__quantum__rt__initialize",
        LLVM::LLVMFunctionType::get(voidType, ptrType, false));
  }

  auto main = module.lookupSymbol<LLVM::LLVMFuncOp>("main");
  if (!main) {
    module.emitError("expected an LLVM @main() -> i64 entry point");
    return failure();
  }

  builder.setInsertionPointToStart(&main.getBody().front());
  Type ptrType = LLVM::LLVMPointerType::get(builder.getContext());
  Value null = LLVM::ZeroOp::create(builder, main.getLoc(), ptrType);

  LLVM::CallOp::create(
    builder,
    main.getLoc(),
    TypeRange{},
    FlatSymbolRefAttr::get(builder.getContext(), "__quantum__rt__initialize"),
    null
  );

  return success();
}

struct FinalizeQIRLLVMPass final
  : PassWrapper<FinalizeQIRLLVMPass, OperationPass<ModuleOp>> {

  StringRef getArgument() const final { return "finalize-qir-llvm"; }
  StringRef getDescription() const final {
    return "Finalize QIR declarations and LLVM entry point";
  }

  void runOnOperation() override {
    ModuleOp module = getOperation();
    OpBuilder builder(&getContext());

    auto mode = resourceManagementMode(module);
    if (failed(mode)) {
      signalPassFailure();
      return;
    }

    auto result = useDirectResultBuffer(module);
    if (failed(result)) {
      signalPassFailure();
      return;
    }

    result = addEntrypointAttributes(module, builder, *mode);
    if (failed(result)) {
      signalPassFailure();
      return;
    }

    result = addDeclarationAttributes(module, builder);
    if (failed(result)) {
      signalPassFailure();
      return;
    }

    result = instrumentEntryPoint(module, builder);
    if (failed(result)) {
      signalPassFailure();
      return;
    }
  }

};

} // namespace

std::unique_ptr<Pass> mlir::jasp::createFinalizeQIRLLVMPass() {
  return std::make_unique<FinalizeQIRLLVMPass>();
}
