#include "JaspToQIR/JaspToQIR.h"

#include "Jasp/IR/JaspOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/Func/Transforms/FuncConversions.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/Dialect/SCF/Transforms/Patterns.h"
#include "mlir/Dialect/Tensor/IR/Tensor.h"
#include "mlir/IR/BuiltinDialect.h"
#include "mlir/IR/Matchers.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Transforms/DialectConversion.h"
#include "llvm/Support/CommandLine.h"

using namespace mlir;

namespace {

namespace jasp_ir = ::jasp;

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

/// Converts a Jasp gate name to a QIR gate specification.
const GateSpec *findGate(StringRef name) {
  for (const GateSpec &gate : kGates) {
    if (gate.source == name) {
      return &gate;
    }
  }
  return nullptr;
}

/// Builds the lowered representation of a Jasp qubit array. Static mode uses
/// `{base:i64, size:i64}` while dynamic mode uses `{buffer:ptr, size:i64}`.
LLVM::LLVMStructType llvmQubitArrayType(MLIRContext *context, bool dynamic) {
  Type i64 = IntegerType::get(context, 64);
  Type base = dynamic ? Type(LLVM::LLVMPointerType::get(context)) : i64;
  return LLVM::LLVMStructType::getLiteral(context, {base, i64});
}

/// Finds an LLVM declaration in the enclosing module or inserts one with the
/// requested signature at the beginning of that module.
LLVM::LLVMFuncOp getOrDeclareFunction(OpBuilder &builder, Location location,
                                      StringRef name, Type resultType,
                                      TypeRange argumentTypes) {
  // Get the surrounding module
  ModuleOp module =
      builder.getInsertionBlock()->getParentOp()->getParentOfType<ModuleOp>();
  if (!module) {
    module = cast<ModuleOp>(builder.getInsertionBlock()->getParentOp());
  }

  // Try to find function with the given name
  if (auto function = module.lookupSymbol<LLVM::LLVMFuncOp>(name)) {
    return function;
  }

  // If function doesn't exist, then create it with the given type signature
  OpBuilder::InsertionGuard guard(builder);
  builder.setInsertionPointToStart(module.getBody());
  auto functionType = LLVM::LLVMFunctionType::get(resultType,
      SmallVector<Type>(argumentTypes.begin(), argumentTypes.end()), false);
  return LLVM::LLVMFuncOp::create(builder, location, name, functionType);
}

/// Declares, if necessary, and emits a call to a QIR function whose name
/// is formed from the gate name and specialization suffix.
void emitQisCall(OpBuilder &builder, Location location, StringRef gate,
                 ValueRange arguments, StringRef suffix = "__body") {
  std::string name = (llvm::Twine("__quantum__qis__") + gate + suffix).str();
  getOrDeclareFunction(builder, location, name,
                       LLVM::LLVMVoidType::get(builder.getContext()),
                       arguments.getTypes());
  LLVM::CallOp::create(builder, location, TypeRange{},
                       FlatSymbolRefAttr::get(builder.getContext(), name),
                       arguments);
}

/// Declares and emits a QIR runtime call.
LLVM::CallOp emitRuntimeCall(OpBuilder &builder, Location location,
                             StringRef name, TypeRange resultTypes,
                             ValueRange arguments) {
  Type resultType = resultTypes.empty()
                        ? Type(LLVM::LLVMVoidType::get(builder.getContext()))
                        : resultTypes.front();
  getOrDeclareFunction(builder, location, name, resultType,
                       arguments.getTypes());
  return LLVM::CallOp::create(
      builder, location, resultTypes,
      FlatSymbolRefAttr::get(builder.getContext(), name), arguments);
}

/// Materializes a signed 64-bit LLVM integer constant used by QIR handles and
/// qubit-array bookkeeping.
Value llvmConstant(OpBuilder &builder, Location location, int64_t value) {
  return LLVM::ConstantOp::create(builder, location, builder.getI64Type(),
                                  builder.getI64IntegerAttr(value));
}

/// Convert a static integer to an opaque LLVM ptr.
Value llvmIntToPtr(OpBuilder &builder, Location location, int64_t id) {
  return LLVM::IntToPtrOp::create(
      builder, location, LLVM::LLVMPointerType::get(builder.getContext()),
      llvmConstant(builder, location, id));
}

/// Returns a pointer to a module-level `bit_<n>` output label, creating the
/// global string constant if necessary.
Value outputLabel(OpBuilder &builder, Location location, int64_t index) {
  ModuleOp module =
      builder.getInsertionBlock()->getParentOp()->getParentOfType<ModuleOp>();
  if (!module) {
    module = cast<ModuleOp>(builder.getInsertionBlock()->getParentOp());
  }

  std::string name = (llvm::Twine("label") + llvm::Twine(index)).str();
  if (!module.lookupSymbol<LLVM::GlobalOp>(name)) {
    std::string value = (llvm::Twine("bit_") + llvm::Twine(index)).str();
    value.push_back('\0');
    Type type = LLVM::LLVMArrayType::get(builder.getI8Type(), value.size());
    OpBuilder::InsertionGuard guard(builder);
    builder.setInsertionPointToStart(module.getBody());
    LLVM::GlobalOp::create(builder, location, type, true,
                           LLVM::Linkage::Internal, name,
                           builder.getStringAttr(value));
  }

  return LLVM::AddressOfOp::create(
      builder, location, LLVM::LLVMPointerType::get(builder.getContext()),
      name);
}

void recordResult(OpBuilder &builder, Location location, Value result,
                  int64_t outputIndex) {
  Value label = outputLabel(builder, location, outputIndex);
  emitRuntimeCall(builder, location, "__quantum__rt__result_record_output",
                  TypeRange{}, ValueRange{result, label});
}

Value pointerElement(OpBuilder &builder, Location location, Value buffer,
                     Value index) {
  Type pointerType = LLVM::LLVMPointerType::get(builder.getContext());
  Value address = LLVM::GEPOp::create(builder, location, pointerType,
                                      pointerType, buffer, ValueRange{index});
  return LLVM::LoadOp::create(builder, location, pointerType, address, 8);
}

Value fixedPointerBuffer(OpBuilder &builder, Location location, int64_t count) {
  Type pointerType = LLVM::LLVMPointerType::get(builder.getContext());
  Type arrayType = LLVM::LLVMArrayType::get(pointerType, count);
  return LLVM::AllocaOp::create(builder, location, pointerType, arrayType,
                                llvmConstant(builder, location, 1), 8);
}

Block *functionEntryBlock(Operation *operation) {
  if (auto function = operation->getParentOfType<func::FuncOp>()) {
    return &function.getBody().front();
  }
  if (auto function = operation->getParentOfType<LLVM::LLVMFuncOp>()) {
    return &function.getBody().front();
  }
  return nullptr;
}

void releaseAtFunctionReturns(Operation *operation, StringRef name,
                              ValueRange arguments) {
  Operation *function = operation->getParentOfType<func::FuncOp>();
  if (!function) {
    function = operation->getParentOfType<LLVM::LLVMFuncOp>();
  }
  assert(function && "expected measurement inside a function");

  SmallVector<Operation *> returns;
  function->walk([&](Operation *nested) {
    if (isa<func::ReturnOp, LLVM::ReturnOp>(nested)) {
      returns.push_back(nested);
    }
  });
  for (Operation *returnOp : returns) {
    OpBuilder builder(returnOp);
    emitRuntimeCall(builder, returnOp->getLoc(), name, TypeRange{}, arguments);
  }
}

bool isInsideLoop(Operation *operation) {
  return operation->getParentOfType<scf::ForOp>() ||
         operation->getParentOfType<scf::ParallelOp>() ||
         operation->getParentOfType<scf::WhileOp>();
}

/// Measures one qubit into its assigned QIR result slot and reads the slot
/// immediately, returning the resulting i1 value.
Value measureStaticQubit(OpBuilder &builder, Location location, Value qubit,
                         int64_t resultId) {

  // Measure qubit into result
  Value result = llvmIntToPtr(builder, location, resultId);
  emitQisCall(builder, location, "mz", ValueRange{qubit, result});
  recordResult(builder, location, result, resultId);

  // Read result into an LLVM i1
  constexpr StringLiteral readResultName = "__quantum__rt__read_result";
  getOrDeclareFunction(builder, location, readResultName, builder.getI1Type(),
                       TypeRange{result.getType()});
  return LLVM::CallOp::create(builder, location,
        TypeRange{builder.getI1Type()},
        FlatSymbolRefAttr::get(builder.getContext(), readResultName), result)
      .getResult();
}

template <typename OpTy> struct PassState final : OpConversionPattern<OpTy> {
  using OpConversionPattern<OpTy>::OpConversionPattern;
  LogicalResult
  matchAndRewrite(OpTy op, typename OpTy::Adaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {
    Value state = adaptor.getOperands().empty()
                      ? arith::ConstantOp::create(rewriter, op.getLoc(),
                                                  rewriter.getBoolAttr(true))
                            .getResult()
                      : adaptor.getOperands().back();
    rewriter.replaceOp(op, state);
    return success();
  }
};

struct LowerCreateQubits final : OpConversionPattern<jasp_ir::CreateQubitsOp> {
  LowerCreateQubits(TypeConverter &converter, MLIRContext *context,
                    bool dynamic)
      : OpConversionPattern(converter, context), dynamic(dynamic) {}
  LogicalResult
  matchAndRewrite(jasp_ir::CreateQubitsOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {
    auto type = llvmQubitArrayType(rewriter.getContext(), dynamic);

    // Create an llvm struct to hold the qubit array base/size
    Value arrayStruct = LLVM::UndefOp::create(rewriter, op.getLoc(), type);

    Value size = adaptor.getAmount();

    Value base;
    if (dynamic) {
      Type pointerType = LLVM::LLVMPointerType::get(rewriter.getContext());
      int64_t count = op->getAttrOfType<IntegerAttr>("qir.count").getInt();
      base = fixedPointerBuffer(rewriter, op.getLoc(), count);
      Value null = LLVM::ZeroOp::create(rewriter, op.getLoc(), pointerType);
      emitRuntimeCall(rewriter, op.getLoc(),
                      "__quantum__rt__qubit_array_allocate", TypeRange{},
                      ValueRange{size, base, null});
    } else {
      base = llvmConstant(
          rewriter, op.getLoc(),
          op->getAttrOfType<IntegerAttr>("qir.base").getInt());
    }

    // Insert qubit array base index at the struct's index 0
    arrayStruct = LLVM::InsertValueOp::create(
        rewriter, op.getLoc(), arrayStruct, base, ArrayRef<int64_t>{0});

    // Insert qubit array size at the struct's index 1
    arrayStruct = LLVM::InsertValueOp::create(
        rewriter, op.getLoc(), arrayStruct, size, ArrayRef<int64_t>{1});

    rewriter.replaceOp(op, {arrayStruct, adaptor.getQstIn()});
    return success();
  }

private:
  bool dynamic;
};

struct LowerGetQubit final : OpConversionPattern<jasp_ir::GetQubitOp> {
  LowerGetQubit(TypeConverter &converter, MLIRContext *context, bool dynamic)
      : OpConversionPattern(converter, context), dynamic(dynamic) {}
  LogicalResult
  matchAndRewrite(jasp_ir::GetQubitOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {

    // The base of the qubit array is the at index 0 of the llvm struct
    Value base = LLVM::ExtractValueOp::create(
        rewriter, op.getLoc(), adaptor.getQbArray(), ArrayRef<int64_t>{0});

    if (dynamic) {
      rewriter.replaceOp(op, pointerElement(rewriter, op.getLoc(), base,
                                            adaptor.getPosition()));
    } else {
      Value id = LLVM::AddOp::create(rewriter, op.getLoc(), base,
                                     adaptor.getPosition());
      rewriter.replaceOpWithNewOp<LLVM::IntToPtrOp>(
          op, LLVM::LLVMPointerType::get(rewriter.getContext()), id);
    }
    return success();
  }

private:
  bool dynamic;
};

struct LowerDeleteQubits final
    : OpConversionPattern<jasp_ir::DeleteQubitsOp> {
  LowerDeleteQubits(TypeConverter &converter, MLIRContext *context,
                    bool dynamic)
      : OpConversionPattern(converter, context), dynamic(dynamic) {}

  LogicalResult
  matchAndRewrite(jasp_ir::DeleteQubitsOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {
    if (dynamic) {
      Value buffer = LLVM::ExtractValueOp::create(
          rewriter, op.getLoc(), adaptor.getQubits(), ArrayRef<int64_t>{0});
      Value size = LLVM::ExtractValueOp::create(
          rewriter, op.getLoc(), adaptor.getQubits(), ArrayRef<int64_t>{1});
      emitRuntimeCall(rewriter, op.getLoc(),
                      "__quantum__rt__qubit_array_release", TypeRange{},
                      ValueRange{size, buffer});
    }
    rewriter.replaceOp(op, adaptor.getInQst());
    return success();
  }

private:
  bool dynamic;
};

struct LowerGetSize final : OpConversionPattern<jasp_ir::GetSizeOp> {
  using OpConversionPattern::OpConversionPattern;
  LogicalResult
  matchAndRewrite(jasp_ir::GetSizeOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {
    rewriter.replaceOpWithNewOp<LLVM::ExtractValueOp>(op, adaptor.getQbArray(),
                                                      ArrayRef<int64_t>{1});
    return success();
  }
};

struct LowerReset final : OpConversionPattern<jasp_ir::ResetOp> {
  LowerReset(TypeConverter &converter, MLIRContext *context, bool dynamic)
      : OpConversionPattern(converter, context), dynamic(dynamic) {}
  LogicalResult
  matchAndRewrite(jasp_ir::ResetOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {
    Value qubits = adaptor.getQubits();

    // Single qubit case
    if (isa<LLVM::LLVMPointerType>(qubits.getType())) {
      emitQisCall(rewriter, op.getLoc(), "reset", qubits);

    // Qubit array case
    } else {
      Value base = LLVM::ExtractValueOp::create(rewriter, op.getLoc(), qubits,
                                                ArrayRef<int64_t>{0});
      Value size = LLVM::ExtractValueOp::create(rewriter, op.getLoc(), qubits,
                                                ArrayRef<int64_t>{1});
      Value zero = llvmConstant(rewriter, op.getLoc(), 0);
      Value one = llvmConstant(rewriter, op.getLoc(), 1);
      constexpr StringLiteral resetName = "__quantum__qis__reset__body";
      auto pointerType = LLVM::LLVMPointerType::get(rewriter.getContext());
      getOrDeclareFunction(rewriter, op.getLoc(), resetName,
                          LLVM::LLVMVoidType::get(rewriter.getContext()),
                          TypeRange{pointerType});
      scf::ForOp::create(
          rewriter, op.getLoc(), zero, size, one, ValueRange{},
          [&](OpBuilder &builder, Location location, Value index, ValueRange) {
            Value qubit;
            if (dynamic) {
              qubit = pointerElement(builder, location, base, index);
            } else {
              Value id = LLVM::AddOp::create(builder, location, base, index);
              qubit = LLVM::IntToPtrOp::create(builder, location, pointerType,
                                               id);
            }
            LLVM::CallOp::create(
                builder, location, TypeRange{},
                FlatSymbolRefAttr::get(builder.getContext(), resetName), qubit);
            scf::YieldOp::create(builder, location);
          });
    }
    rewriter.replaceOp(op, adaptor.getInQst());
    return success();
  }

private:
  bool dynamic;
};

struct LowerGate final : OpConversionPattern<jasp_ir::QuantumGateOp> {
  using OpConversionPattern::OpConversionPattern;
  LogicalResult
  matchAndRewrite(jasp_ir::QuantumGateOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {
    const GateSpec *spec = findGate(op.getGateType());
    if (!spec) {
      return rewriter.notifyMatchFailure(op, "unsupported gate");
    }
    SmallVector<Value> arguments(adaptor.getGateOperands());

    // The arguments in Jasp MLIR (qubit, angle) are in the reverse order
    // as QIS-QIR (angle, qubit)
    if (spec->rotation && arguments.size() == 2) {
      std::swap(arguments[0], arguments[1]);
    }
    emitQisCall(rewriter, op.getLoc(), spec->qir, arguments, spec->suffix);
    rewriter.replaceOp(op, adaptor.getInQst());
    return success();
  }
};

struct LowerMeasure final : OpConversionPattern<jasp_ir::MeasureOp> {
  LowerMeasure(TypeConverter &converter, MLIRContext *context, bool dynamic)
      : OpConversionPattern(converter, context), dynamic(dynamic) {}
  LogicalResult
  matchAndRewrite(jasp_ir::MeasureOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {
    int64_t resultBase =
        op->getAttrOfType<IntegerAttr>("qir.result_base").getInt();
    Value qubits = adaptor.getMeasQ();
    if (isa<LLVM::LLVMPointerType>(qubits.getType())) {
      Value bit;
      if (dynamic) {
        Type pointerType = LLVM::LLVMPointerType::get(rewriter.getContext());
        Block *entry = functionEntryBlock(op);
        if (!entry) {
          return rewriter.notifyMatchFailure(op, "expected enclosing function");
        }
        Value result;
        {
          OpBuilder::InsertionGuard guard(rewriter);
          rewriter.setInsertionPointToStart(entry);
          Value null = LLVM::ZeroOp::create(rewriter, op.getLoc(), pointerType);
          result = emitRuntimeCall(rewriter, op.getLoc(),
                                   "__quantum__rt__result_allocate",
                                   TypeRange{pointerType}, ValueRange{null})
                       .getResult();
        }
        emitQisCall(rewriter, op.getLoc(), "mz", ValueRange{qubits, result});
        recordResult(rewriter, op.getLoc(), result, resultBase);
        constexpr StringLiteral readResultName =
            "__quantum__rt__read_result";
        bit = emitRuntimeCall(rewriter, op.getLoc(), readResultName,
                              TypeRange{rewriter.getI1Type()},
                              ValueRange{result})
                  .getResult();
        if (isInsideLoop(op)) {
          releaseAtFunctionReturns(op, "__quantum__rt__result_release",
                                   result);
        } else {
          emitRuntimeCall(rewriter, op.getLoc(),
                          "__quantum__rt__result_release", TypeRange{}, result);
        }
      } else {
        bit = measureStaticQubit(rewriter, op.getLoc(), qubits, resultBase);
      }
      rewriter.replaceOp(op, {bit, adaptor.getInQst()});
      return success();
    }

    int64_t count = op->getAttrOfType<IntegerAttr>("qir.count").getInt();
    Value base = LLVM::ExtractValueOp::create(rewriter, op.getLoc(), qubits,
                                              ArrayRef<int64_t>{0});
    Type pointerType = LLVM::LLVMPointerType::get(rewriter.getContext());
    Value resultBuffer;
    Value dynamicCount;
    if (dynamic) {
      Block *entry = functionEntryBlock(op);
      if (!entry) {
        return rewriter.notifyMatchFailure(op, "expected enclosing function");
      }
      {
        OpBuilder::InsertionGuard guard(rewriter);
        rewriter.setInsertionPointToStart(entry);
        dynamicCount = llvmConstant(rewriter, op.getLoc(), count);
        resultBuffer = fixedPointerBuffer(rewriter, op.getLoc(), count);
        Value null = LLVM::ZeroOp::create(rewriter, op.getLoc(), pointerType);
        emitRuntimeCall(rewriter, op.getLoc(),
                        "__quantum__rt__result_array_allocate", TypeRange{},
                        ValueRange{dynamicCount, resultBuffer, null});
      }
      for (int64_t index = 0; index < count; ++index) {
        Value offset = llvmConstant(rewriter, op.getLoc(), index);
        Value qubit = pointerElement(rewriter, op.getLoc(), base, offset);
        Value result =
            pointerElement(rewriter, op.getLoc(), resultBuffer, offset);
        emitQisCall(rewriter, op.getLoc(), "mz", ValueRange{qubit, result});
      }
      Value label = outputLabel(rewriter, op.getLoc(), resultBase);
      emitRuntimeCall(rewriter, op.getLoc(),
                      "__quantum__rt__result_array_record_output", TypeRange{},
                      ValueRange{dynamicCount, resultBuffer, label});
    }

    Value packed = llvmConstant(rewriter, op.getLoc(), 0);
    for (int64_t index = 0; index < count; ++index) {
      Value offset = llvmConstant(rewriter, op.getLoc(), index);
      Value bit;
      if (dynamic) {
        Value result =
            pointerElement(rewriter, op.getLoc(), resultBuffer, offset);
        bit = emitRuntimeCall(rewriter, op.getLoc(),
                              "__quantum__rt__read_result",
                              TypeRange{rewriter.getI1Type()},
                              ValueRange{result})
                  .getResult();
      } else {
        Value id = LLVM::AddOp::create(rewriter, op.getLoc(), base, offset);
        Value qubit = LLVM::IntToPtrOp::create(
            rewriter, op.getLoc(), pointerType, id);
        bit = measureStaticQubit(rewriter, op.getLoc(), qubit,
                                 resultBase + index);
      }
      Value extended = LLVM::ZExtOp::create(rewriter, op.getLoc(),
                                            rewriter.getI64Type(), bit);
      Value shifted =
          LLVM::ShlOp::create(rewriter, op.getLoc(), extended,
                              llvmConstant(rewriter, op.getLoc(), index));
      packed = LLVM::OrOp::create(rewriter, op.getLoc(), packed, shifted);
    }
    if (dynamic) {
      if (isInsideLoop(op)) {
        releaseAtFunctionReturns(
            op, "__quantum__rt__result_array_release",
            ValueRange{dynamicCount, resultBuffer});
      } else {
        emitRuntimeCall(rewriter, op.getLoc(),
                        "__quantum__rt__result_array_release", TypeRange{},
                        ValueRange{dynamicCount, resultBuffer});
      }
    }
    rewriter.replaceOp(op, {packed, adaptor.getInQst()});
    return success();
  }

private:
  bool dynamic;
};

/// Converts
///   arith.constant dense<3> : tensor<i64>
/// to
///   arith.constant 3 : i64
struct ScalarConstant final : OpConversionPattern<arith::ConstantOp> {
  using OpConversionPattern::OpConversionPattern;
  LogicalResult
  matchAndRewrite(arith::ConstantOp op, OpAdaptor,
                  ConversionPatternRewriter &rewriter) const override {
    auto tensor = dyn_cast<RankedTensorType>(op.getType());
    auto dense = dyn_cast<DenseElementsAttr>(op.getValue());
    if (!tensor || tensor.getRank() != 0 || !dense) {
      return failure();
    }
    rewriter.replaceOpWithNewOp<arith::ConstantOp>(
        op, tensor.getElementType(), dense.getSplatValue<TypedAttr>());
    return success();
  }
};

/// Converts
///   %scalar = tensor.extract %tensor[] : tensor<i64>
/// to simply the converted scalar value of %tensor.
struct ScalarExtract final : OpConversionPattern<tensor::ExtractOp> {
  using OpConversionPattern::OpConversionPattern;
  LogicalResult
  matchAndRewrite(tensor::ExtractOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {
    auto tensor = dyn_cast<RankedTensorType>(op.getTensor().getType());
    if (!tensor || tensor.getRank() != 0 || !op.getIndices().empty()) {
      return failure();
    }
    rewriter.replaceOp(op, adaptor.getTensor());
    return success();
  }
};

/// Converts
///   %tensor = tensor.from_elements %value : tensor<i64>
/// to simply use %value.
struct ScalarFromElements final : OpConversionPattern<tensor::FromElementsOp> {
  using OpConversionPattern::OpConversionPattern;
  LogicalResult
  matchAndRewrite(tensor::FromElementsOp op, OpAdaptor adaptor,
                  ConversionPatternRewriter &rewriter) const override {
    auto tensor = dyn_cast<RankedTensorType>(op.getType());
    if (!tensor || tensor.getRank() != 0 || adaptor.getElements().size() != 1) {
      return failure();
    }
    rewriter.replaceOp(op, adaptor.getElements().front());
    return success();
  }
};

/// Reports whether a type is f64 directly or through a ranked tensor element.
bool containsFloat(Type type) {
  if (type.isF64()) {
    return true;
  }
  if (auto tensor = dyn_cast<RankedTensorType>(type)) {
    return tensor.getElementType().isF64();
  }
  return false;
}

/// Returns whether a Jasp operation has an explicit lowering in this pass.
bool isSupportedJaspOp(Operation *op) {
  return isa<jasp_ir::CreateQuantumKernelOp, jasp_ir::ConsumeQuantumKernelOp,
             jasp_ir::CreateQubitsOp, jasp_ir::DeleteQubitsOp,
             jasp_ir::GetQubitOp, jasp_ir::GetSizeOp, jasp_ir::QuantumGateOp,
             jasp_ir::MeasureOp, jasp_ir::ResetOp>(op);
}

/// Rewrites Jasp's state-threaded `main` into the zero-argument QIR entry
/// point convention and normalizes each return value to QIR's i64 status code.
LogicalResult prepareMain(ModuleOp module) {
  auto main = module.lookupSymbol<func::FuncOp>("main");
  if (!main) {
    return module.emitError("expected a @main function");
  }
  if (main.getNumArguments() != 1 ||
      !isa<jasp_ir::QuantumStateType>(main.getArgument(0).getType())) {
    return main.emitError("expected one Jasp state argument on @main");
  }

  OpBuilder builder(&main.getBody().front(), main.getBody().front().begin());
  Value state = arith::ConstantOp::create(builder, main.getLoc(),
                                          builder.getBoolAttr(true));
  main.getArgument(0).replaceAllUsesWith(state);
  if (failed(main.eraseArgument(0))) {
    return main.emitError("could not remove the Jasp state argument");
  }
  main.setFunctionType(builder.getFunctionType({}, builder.getI64Type()));

  main.walk([&](func::ReturnOp returnOp) {
    OpBuilder returnBuilder(returnOp);
    Value exit = arith::ConstantOp::create(returnBuilder, returnOp.getLoc(),
                                           returnBuilder.getI64IntegerAttr(0));
    returnOp->setOperands(exit);
  });
  return success();
}

struct JaspToQIRPass final
    : PassWrapper<JaspToQIRPass, OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(JaspToQIRPass)

  JaspToQIRPass() = default;
  JaspToQIRPass(const JaspToQIRPass &other) : PassWrapper(other) {
    resourceManagement = other.resourceManagement;
  }

  StringRef getArgument() const final { return "lower-jasp-to-qir"; }
  StringRef getDescription() const final {
    return "Lower typed Jasp operations before standard LLVM conversion";
  }

  Option<std::string> resourceManagement{
      *this, "resource-management",
      llvm::cl::desc("QIR resource management mode: static or dynamic"),
      llvm::cl::init("static")};

  void runOnOperation() override {
    MLIRContext &context = getContext();
    context.loadDialect<arith::ArithDialect, func::FuncDialect,
                        jasp_ir::JaspDialect, LLVM::LLVMDialect,
                        scf::SCFDialect, tensor::TensorDialect>();

    if (resourceManagement != "static" && resourceManagement != "dynamic") {
      getOperation().emitError()
          << "resource-management must be 'static' or 'dynamic'";
      signalPassFailure();
      return;
    }
    bool dynamic = resourceManagement == "dynamic";

    int64_t nextQubit = 0;
    int64_t nextResult = 0;
    int64_t functionCount = 0;
    int64_t mainReturnCount = 0;
    bool hasLoop = false;
    bool hasSwitch = false;
    bool hasFloat = false;
    DenseMap<Value, int64_t> qubitArraySizes;

    // Walk over the MLIR program, gathering information about the required QIR
    // properties, mapping qubit (and qubit array) values to indices, and
    // catching errors.
    WalkResult analysis = getOperation().walk([&](Operation *operation) {
      hasLoop |= isa<scf::ForOp, scf::ParallelOp, scf::WhileOp>(operation);
      hasSwitch |= isa<scf::IndexSwitchOp>(operation);
      for (Type type : operation->getOperandTypes()) {
        hasFloat |= containsFloat(type);
      }
      for (Type type : operation->getResultTypes()) {
        hasFloat |= containsFloat(type);
      }

      // func.FuncOp
      if (auto function = dyn_cast<func::FuncOp>(operation)) {
        ++functionCount;
        (void)function;

      // func.ReturnOp
      } else if (auto returnOp = dyn_cast<func::ReturnOp>(operation)) {
        if (returnOp->getParentOfType<func::FuncOp>().getSymName() == "main") {
          ++mainReturnCount;
        }

      // jasp.CreateQubitsOp
      } else if (auto create = dyn_cast<jasp_ir::CreateQubitsOp>(operation)) {
        APInt numQubitsValue;
        if (!matchPattern(create.getAmount(), m_ConstantInt(&numQubitsValue))) {
          create.emitError("QIR array backing storage requires a "
                           "compile-time constant size");
          return WalkResult::interrupt();
        }
        int64_t numQubits = numQubitsValue.getSExtValue();
        if (!dynamic) {
          create->setAttr(
              "qir.base",
              IntegerAttr::get(IntegerType::get(&context, 64), nextQubit));
        }
        create->setAttr(
            "qir.count",
            IntegerAttr::get(IntegerType::get(&context, 64), numQubits));
        qubitArraySizes[create.getResult()] = numQubits;
        nextQubit += numQubits;

      // jasp.MeasureOp
      } else if (auto measure = dyn_cast<jasp_ir::MeasureOp>(operation)) {
        int64_t count = 1;
        Value qubitArg = measure.getMeasQ();
        if (isa<jasp_ir::QubitArrayType>(qubitArg.getType())) {
          auto mapPair = qubitArraySizes.find(qubitArg);
          if (mapPair == qubitArraySizes.end()) {
            measure.emitError("Could not statically determine size of measured "
                              "qubit array");
            return WalkResult::interrupt();
          }
          count = mapPair->second;
        }
        measure->setAttr(
            "qir.result_base",
            IntegerAttr::get(IntegerType::get(&context, 64), nextResult));
        measure->setAttr(
            "qir.count",
            IntegerAttr::get(IntegerType::get(&context, 64), count));
        nextResult += count;

      // jasp.QuantumGateOp
      } else if (auto gate = dyn_cast<jasp_ir::QuantumGateOp>(operation)) {
        if (!findGate(gate.getGateType())) {
          gate.emitError() << "Unsupported Jasp gate '" << gate.getGateType()
                           << "'";
          return WalkResult::interrupt();
        }

      // jasp.SomeUnsupportedOperation
      } else if (operation->getDialect() &&
                 operation->getDialect()->getNamespace() == "jasp" &&
                 !isSupportedJaspOp(operation)) {
        operation->emitError()
            << "Unsupported Jasp operation '" << operation->getName() << "'";
        return WalkResult::interrupt();
      }

      return WalkResult::advance();
    });

    if (analysis.wasInterrupted() || failed(prepareMain(getOperation()))) {
      signalPassFailure();
      return;
    }


    // These are QIR attributes. We store them in MLIR as module attributes.
    ModuleOp module = getOperation();
    auto i64 = IntegerType::get(&context, 64);
    module->setAttr("jasp.resource_management",
                    StringAttr::get(&context, resourceManagement));
    if (!dynamic) {
      module->setAttr("jasp.required_num_qubits",
                      IntegerAttr::get(i64, nextQubit));
      module->setAttr("jasp.required_num_results",
                      IntegerAttr::get(i64, nextResult));
    }
    module->setAttr("jasp.ir_functions",
                    BoolAttr::get(&context, functionCount > 1));
    module->setAttr("jasp.backwards_branching",
                    BoolAttr::get(&context, hasLoop));
    module->setAttr("jasp.multiple_target_branching",
                    BoolAttr::get(&context, hasSwitch));
    module->setAttr("jasp.multiple_return_points",
                    BoolAttr::get(&context, mainReturnCount > 1));
    module->setAttr("jasp.float_computations",
                    BoolAttr::get(&context, hasFloat));


    // Type conversion rules
    TypeConverter converter;

    // default -> do nothing
    converter.addConversion([](Type type) { return type; });

    // tensor -> unwrap rank-0 tensors. do nothing for higher-rank tensors
    converter.addConversion([&](RankedTensorType type) -> std::optional<Type> {
      if (type.getRank() == 0 && (type.getElementType().isInteger() ||
                                  type.getElementType().isF64())) {
        return type.getElementType();
      }
      return std::nullopt; // don't know how to convert
    });

    // quantum state -> dummy type, relying on QIR's side effects
    converter.addConversion([&](jasp_ir::QuantumStateType) -> Type {
      return IntegerType::get(&context, 1);
    });

    // qubit -> opaque ptr type in QIR
    converter.addConversion([&](jasp_ir::QubitType) -> Type {
      return LLVM::LLVMPointerType::get(&context);
    });

    // qubit array -> static {base:i64, size:i64} or dynamic {ptr, size:i64}
    converter.addConversion([&](jasp_ir::QubitArrayType) -> Type {
      return llvmQubitArrayType(&context, dynamic);
    });


    ConversionTarget target(context);

    // Allow builtin and LLVM dialects
    target.addLegalDialect<BuiltinDialect, LLVM::LLVMDialect>();

    // Disallow Jasp and tensor dialects (these must be converted)
    target.addIllegalDialect<jasp_ir::JaspDialect, tensor::TensorDialect>();

    // Allow arith and func dialects, only if their operand Atypes are already
    // converted. For example, `arith.addi` using `tensor<i64>` is illegal
    // unless its tensor type is converted to a scalar.
    target.addDynamicallyLegalDialect<arith::ArithDialect>(
        [&](Operation *op) { return converter.isLegal(op); });
    target.addDynamicallyLegalDialect<func::FuncDialect>(
        [&](Operation *op) { return converter.isLegal(op); });

    // Ensure that function signatures and bodies are converted and legal
    target.addDynamicallyLegalOp<func::FuncOp>([&](func::FuncOp function) {
      return converter.isSignatureLegal(function.getFunctionType()) &&
             converter.isLegal(&function.getBody());
    });

    RewritePatternSet patterns(&context);
    patterns
        .add<PassState<jasp_ir::CreateQuantumKernelOp>,
             PassState<jasp_ir::ConsumeQuantumKernelOp>,
             LowerGetSize, LowerGate,
             ScalarConstant, ScalarExtract, ScalarFromElements>(converter,
                                                                &context);
    patterns.add<LowerCreateQubits, LowerDeleteQubits, LowerGetQubit,
                 LowerReset, LowerMeasure>(converter, &context, dynamic);
    populateFunctionOpInterfaceTypeConversionPattern<func::FuncOp>(patterns,
                                                                   converter);
    populateCallOpTypeConversionPattern(patterns, converter);
    populateReturnOpTypeConversionPattern(patterns, converter);
    scf::populateSCFStructuralTypeConversionsAndLegality(converter, patterns,
                                                         target);

    if (failed(applyFullConversion(module, target, std::move(patterns)))) {
      signalPassFailure();
    }
  }
};

} // namespace

std::unique_ptr<Pass> mlir::jasp::createJaspToQIRPass() {
  return std::make_unique<JaspToQIRPass>();
}
