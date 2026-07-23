#include "JaspToQIR/JaspToQIR.h"

#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/IR/Matchers.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Transforms/GreedyPatternRewriteDriver.h"
#include "llvm/ADT/STLExtras.h"

using namespace mlir;

namespace {

constexpr StringLiteral kJaspPrefix = "jasp.";
constexpr StringLiteral kOperations[] = {
    "create_quantum_kernel",
    "consume_quantum_kernel",
    "create_qubits",
    "delete_qubits",
    "get_qubit",
    "get_size",
    "quantum_gate",
    "measure",
    "reset",
};

struct GateSpec {
  StringLiteral source;
  StringLiteral qir;
  StringLiteral suffix;
  bool rotation;
};

constexpr GateSpec kGates[] = {
    {"h", "h", "__body", false},   {"x", "x", "__body", false},
    {"y", "y", "__body", false},   {"z", "z", "__body", false},
    {"s", "s", "__body", false},   {"s_dg", "s", "__adj", false},
    {"t", "t", "__body", false},   {"t_dg", "t", "__adj", false},
    {"rx", "rx", "__body", true},  {"ry", "ry", "__body", true},
    {"rz", "rz", "__body", true},  {"cx", "cnot", "__body", false},
    {"cz", "cz", "__body", false},
};

const GateSpec *findGate(StringRef name) {
  for (const GateSpec &gate : kGates) {
    if (gate.source == name) {
      return &gate;
    }
  }
  return nullptr;
}

bool isSupportedOperation(StringRef name) {
  return llvm::is_contained(kOperations, name);
}

LLVM::LLVMFuncOp getOrCreateFunction(OpBuilder &builder, Location location,
                                     StringRef name, Type result,
                                     TypeRange arguments) {
  Operation *parent = builder.getInsertionBlock()->getParentOp();
  ModuleOp module = dyn_cast<ModuleOp>(parent);
  if (!module) {
    module = parent->getParentOfType<ModuleOp>();
  }

  if (auto function = module.lookupSymbol<LLVM::LLVMFuncOp>(name)) {
    return function;
  }

  LLVM::LLVMFuncOp function;
  {
    OpBuilder::InsertionGuard guard(builder);
    builder.setInsertionPointToStart(module.getBody());
    auto type = LLVM::LLVMFunctionType::get(
        result, SmallVector<Type>(arguments.begin(), arguments.end()), false);
    function = LLVM::LLVMFuncOp::create(builder, location, name, type);
  }
  return function;
}

void emitQisCall(OpBuilder &builder, Location location, StringRef gate,
                 ValueRange arguments, StringRef suffix = "__body") {
  std::string name = (llvm::Twine("__quantum__qis__") + gate + suffix).str();
  getOrCreateFunction(builder, location, name,
                      LLVM::LLVMVoidType::get(builder.getContext()),
                      arguments.getTypes());

  LLVM::CallOp::create(builder, location, TypeRange{},
                       FlatSymbolRefAttr::get(builder.getContext(), name),
                       arguments);
}

Value constant(OpBuilder &builder, Location location, int64_t value) {
  return LLVM::ConstantOp::create(builder, location, builder.getI64Type(),
                                  builder.getI64IntegerAttr(value));
}

Value resultPointer(OpBuilder &builder, Location location, int64_t id) {
  return LLVM::IntToPtrOp::create(
      builder, location, LLVM::LLVMPointerType::get(builder.getContext()),
      constant(builder, location, id));
}

Value measureQubit(OpBuilder &builder, Location location, Value qubit,
                   int64_t resultId) {
  Value result = resultPointer(builder, location, resultId);
  emitQisCall(builder, location, "mz", ValueRange{qubit, result});

  constexpr StringLiteral name = "__quantum__rt__read_result";
  getOrCreateFunction(builder, location, name, builder.getI1Type(),
                      TypeRange{result.getType()});
  return LLVM::CallOp::create(
             builder, location, TypeRange{builder.getI1Type()},
             FlatSymbolRefAttr::get(builder.getContext(), name), result)
      .getResult();
}

struct LowerJaspOp final : RewritePattern {
  LowerJaspOp(StringRef name, MLIRContext *context)
      : RewritePattern(name, 1, context) {}

  LogicalResult matchAndRewrite(Operation *op,
                                PatternRewriter &rewriter) const override {
    StringRef name =
        op->getName().getStringRef().drop_front(kJaspPrefix.size());
    ValueRange operands = op->getOperands();
    Location location = op->getLoc();

    if (name == "create_quantum_kernel" || name == "consume_quantum_kernel") {
      Value state = operands.empty()
                        ? LLVM::ConstantOp::create(rewriter, location,
                                                   rewriter.getI1Type(),
                                                   rewriter.getBoolAttr(true))
                        : operands.back();
      rewriter.replaceOp(op, state);
      return success();
    }

    if (name == "create_qubits") {
      auto arrayType = cast<LLVM::LLVMStructType>(op->getResult(0).getType());
      Value array = LLVM::UndefOp::create(rewriter, location, arrayType);
      Value base =
          constant(rewriter, location,
                   op->getAttrOfType<IntegerAttr>("qir.base").getInt());
      array = LLVM::InsertValueOp::create(rewriter, location, array, base,
                                          ArrayRef<int64_t>{0});
      array = LLVM::InsertValueOp::create(
          rewriter, location, array, operands.front(), ArrayRef<int64_t>{1});
      rewriter.replaceOp(op, {array, operands.back()});
      return success();
    }

    if (name == "delete_qubits") {
      rewriter.replaceOp(op, operands.back());
      return success();
    }

    if (name == "reset") {
      Value qubits = operands.front();
      if (isa<LLVM::LLVMPointerType>(qubits.getType())) {
        emitQisCall(rewriter, location, "reset", qubits);
      } else {
        Value base = LLVM::ExtractValueOp::create(rewriter, location, qubits,
                                                  ArrayRef<int64_t>{0});
        Value size = LLVM::ExtractValueOp::create(rewriter, location, qubits,
                                                  ArrayRef<int64_t>{1});
        Value zero = constant(rewriter, location, 0);
        Value one = constant(rewriter, location, 1);
        constexpr StringLiteral resetName = "__quantum__qis__reset__body";
        auto pointerType = LLVM::LLVMPointerType::get(rewriter.getContext());
        getOrCreateFunction(rewriter, location, resetName,
                            LLVM::LLVMVoidType::get(rewriter.getContext()),
                            TypeRange{pointerType});
        scf::ForOp::create(
            rewriter, location, zero, size, one, ValueRange{},
            [&](OpBuilder &builder, Location bodyLocation, Value index,
                ValueRange) {
              Value id =
                  LLVM::AddOp::create(builder, bodyLocation, base, index);
              Value qubit = LLVM::IntToPtrOp::create(builder, bodyLocation,
                                                     pointerType, id);
              LLVM::CallOp::create(
                  builder, bodyLocation, TypeRange{},
                  FlatSymbolRefAttr::get(builder.getContext(), resetName),
                  qubit);
              scf::YieldOp::create(builder, bodyLocation);
            });
      }
      rewriter.replaceOp(op, operands.back());
      return success();
    }

    if (name == "get_qubit") {
      Value base = LLVM::ExtractValueOp::create(rewriter, location, operands[0],
                                                ArrayRef<int64_t>{0});
      Value id = LLVM::AddOp::create(rewriter, location, base, operands[1]);
      Value qubit = LLVM::IntToPtrOp::create(
          rewriter, location, LLVM::LLVMPointerType::get(rewriter.getContext()),
          id);
      rewriter.replaceOp(op, qubit);
      return success();
    }

    if (name == "get_size") {
      Value size = LLVM::ExtractValueOp::create(
          rewriter, location, operands.front(), ArrayRef<int64_t>{1});
      rewriter.replaceOp(op, size);
      return success();
    }

    if (name == "quantum_gate") {
      auto gate = op->getAttrOfType<StringAttr>("gate_type");
      if (!gate) {
        return rewriter.notifyMatchFailure(op, "missing gate_type attribute");
      }

      const GateSpec *spec = findGate(gate.getValue());
      if (!spec) {
        return rewriter.notifyMatchFailure(op, "unsupported gate");
      }

      SmallVector<Value> arguments(operands.drop_back());
      if (spec->rotation && arguments.size() == 2) {
        std::swap(arguments[0], arguments[1]);
      }
      emitQisCall(rewriter, location, spec->qir, arguments, spec->suffix);
      rewriter.replaceOp(op, operands.back());
      return success();
    }

    if (name == "measure") {
      int64_t resultBase =
          op->getAttrOfType<IntegerAttr>("qir.result_base").getInt();
      if (isa<LLVM::LLVMPointerType>(operands.front().getType())) {
        Value bit =
            measureQubit(rewriter, location, operands.front(), resultBase);
        rewriter.replaceOp(op, {bit, operands.back()});
        return success();
      }

      int64_t count = op->getAttrOfType<IntegerAttr>("qir.count").getInt();
      Value base = LLVM::ExtractValueOp::create(
          rewriter, location, operands.front(), ArrayRef<int64_t>{0});
      Value packed = constant(rewriter, location, 0);
      for (int64_t index = 0; index < count; ++index) {
        Value id = LLVM::AddOp::create(rewriter, location, base,
                                       constant(rewriter, location, index));
        Value qubit = LLVM::IntToPtrOp::create(
            rewriter, location,
            LLVM::LLVMPointerType::get(rewriter.getContext()), id);
        Value bit = measureQubit(rewriter, location, qubit, resultBase + index);
        Value extended = LLVM::ZExtOp::create(rewriter, location,
                                              rewriter.getI64Type(), bit);
        Value shifted = LLVM::ShlOp::create(
            rewriter, location, extended, constant(rewriter, location, index));
        packed = LLVM::OrOp::create(rewriter, location, packed, shifted);
      }
      rewriter.replaceOp(op, {packed, operands.back()});
      return success();
    }

    return rewriter.notifyMatchFailure(op, "unsupported Jasp operation");
  }
};

struct JaspToQIRPass final
    : PassWrapper<JaspToQIRPass, OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(JaspToQIRPass)

  StringRef getArgument() const final { return "lower-jasp-to-qir"; }
  StringRef getDescription() const final {
    return "Lower Jasp operations before standard LLVM conversion";
  }

  void runOnOperation() override {
    getContext().loadDialect<LLVM::LLVMDialect, scf::SCFDialect>();
    int64_t nextQubit = 0;
    int64_t nextResult = 0;
    int64_t functionCount = 0;
    int64_t mainReturnCount = 0;
    bool hasLoop = false;
    bool hasSwitch = false;
    bool hasFloat = false;
    DenseMap<Value, int64_t> arraySizes;
    WalkResult analysis = getOperation().walk([&](Operation *op) {
      StringRef name = op->getName().getStringRef();
      hasLoop |=
          name == "scf.for" || name == "scf.parallel" || name == "scf.while";
      hasSwitch |= name == "scf.index_switch";
      if (name == "jasp.reset" &&
          !isa<LLVM::LLVMPointerType>(op->getOperand(0).getType())) {
        hasLoop = true;
      }
      for (Type type : op->getOperandTypes()) {
        hasFloat |= type.isF64();
      }
      for (Type type : op->getResultTypes()) {
        hasFloat |= type.isF64();
      }

      if (name == "func.func") {
        ++functionCount;

      } else if (name == "func.return") {
        Operation *function = op->getParentOp();
        while (function && function->getName().getStringRef() != "func.func") {
          function = function->getParentOp();
        }
        if (function) {
          if (auto symbol = function->getAttrOfType<StringAttr>("sym_name")) {
            mainReturnCount += symbol.getValue() == "main";
          }
        }

      } else if (name == "jasp.create_qubits") {
        APInt countValue;
        if (!matchPattern(op->getOperand(0), m_ConstantInt(&countValue))) {
          op->emitError("QIR static resource allocation requires a "
                        "constant size");
          return WalkResult::interrupt();
        }
        int64_t count = countValue.getSExtValue();
        op->setAttr(
            "qir.base",
            IntegerAttr::get(IntegerType::get(&getContext(), 64), nextQubit));
        arraySizes[op->getResult(0)] = count;
        nextQubit += count;

      } else if (name == "jasp.measure") {
        int64_t count = 1;
        if (!isa<LLVM::LLVMPointerType>(op->getOperand(0).getType())) {
          auto found = arraySizes.find(op->getOperand(0));
          if (found == arraySizes.end()) {
            op->emitError("cannot determine the statically "
                          "allocated array size");
            return WalkResult::interrupt();
          }
          count = found->second;
        }
        op->setAttr(
            "qir.result_base",
            IntegerAttr::get(IntegerType::get(&getContext(), 64), nextResult));
        op->setAttr(
            "qir.count",
            IntegerAttr::get(IntegerType::get(&getContext(), 64), count));
        nextResult += count;

      } else if (name == "jasp.quantum_gate") {
        auto gate = op->getAttrOfType<StringAttr>("gate_type");
        if (!gate) {
          op->emitError("missing gate_type attribute");
          return WalkResult::interrupt();
        }
        if (!findGate(gate.getValue())) {
          op->emitError() << "unsupported Jasp gate '" << gate.getValue()
                          << "'";
          return WalkResult::interrupt();
        }

      } else if (name.starts_with(kJaspPrefix) &&
                 !isSupportedOperation(name.drop_front(kJaspPrefix.size()))) {
        op->emitError() << "unsupported Jasp operation '" << name << "'";
        return WalkResult::interrupt();
      }

      return WalkResult::advance();
    });
    if (analysis.wasInterrupted()) {
      signalPassFailure();
      return;
    }

    ModuleOp module = getOperation();
    auto i64 = IntegerType::get(&getContext(), 64);
    module->setAttr("jasp.required_num_qubits",
                    IntegerAttr::get(i64, nextQubit));
    module->setAttr("jasp.required_num_results",
                    IntegerAttr::get(i64, nextResult));
    module->setAttr("jasp.ir_functions",
                    BoolAttr::get(&getContext(), functionCount > 1));
    module->setAttr("jasp.backwards_branching",
                    BoolAttr::get(&getContext(), hasLoop));
    module->setAttr("jasp.multiple_target_branching",
                    BoolAttr::get(&getContext(), hasSwitch));
    module->setAttr("jasp.multiple_return_points",
                    BoolAttr::get(&getContext(), mainReturnCount > 1));
    module->setAttr("jasp.float_computations",
                    BoolAttr::get(&getContext(), hasFloat));

    RewritePatternSet patterns(&getContext());
    for (StringRef name : kOperations) {
      patterns.add<LowerJaspOp>((llvm::Twine(kJaspPrefix) + name).str(),
                                &getContext());
    }
    if (failed(applyPatternsGreedily(getOperation(), std::move(patterns)))) {
      signalPassFailure();
    }
  }
};

} // namespace

std::unique_ptr<Pass> mlir::jasp::createJaspToQIRPass() {
  return std::make_unique<JaspToQIRPass>();
}
