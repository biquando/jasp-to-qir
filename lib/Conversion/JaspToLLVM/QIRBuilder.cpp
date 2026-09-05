#include "QIRBuilder.h"

#include "llvm/ADT/Twine.h"
#include "mlir/IR/BuiltinOps.h"

using namespace mlir;

namespace mlir::jasp::internal {

namespace {

ModuleOp getEnclosingModule(OpBuilder &builder)
{
    Operation *parent = builder.getInsertionBlock()->getParentOp();
    if (auto module = dyn_cast<ModuleOp>(parent)) {
        return module;
    }
    return parent->getParentOfType<ModuleOp>();
}

} // namespace

LLVM::LLVMStructType
QIRBuilder::getQubitArrayType(MLIRContext *context,
                              ResourceManagement resourceManagement)
{
    Type i64 = IntegerType::get(context, 64);
    Type base = resourceManagement == ResourceManagement::Dynamic
                  ? Type(LLVM::LLVMPointerType::get(context))
                  : i64;
    return LLVM::LLVMStructType::getLiteral(context, {base, i64});
}

LLVM::LLVMFuncOp QIRBuilder::getOrDeclareFunction(StringRef name,
                                                  TypeRange argumentTypes,
                                                  TypeRange resultTypes)
{
    Type resultType = resultTypes.empty()
                        ? Type(LLVM::LLVMVoidType::get(builder.getContext()))
                        : resultTypes.front();

    ModuleOp module = getEnclosingModule(builder);
    if (auto function = module.lookupSymbol<LLVM::LLVMFuncOp>(name)) {
        return function;
    }

    OpBuilder::InsertionGuard guard(builder);
    builder.setInsertionPointToStart(module.getBody());
    auto functionType = LLVM::LLVMFunctionType::get(
        resultType,
        SmallVector<Type>(argumentTypes.begin(), argumentTypes.end()),
        false);
    return LLVM::LLVMFuncOp::create(builder, location, name, functionType);
}

LLVM::CallOp
QIRBuilder::call(StringRef name, ValueRange arguments, TypeRange resultTypes)
{
    getOrDeclareFunction(name, arguments.getTypes(), resultTypes);
    return callDeclared(name, arguments, resultTypes);
}

LLVM::CallOp QIRBuilder::callDeclared(StringRef name,
                                      ValueRange arguments,
                                      TypeRange resultTypes)
{
    return LLVM::CallOp::create(
        builder,
        location,
        resultTypes,
        FlatSymbolRefAttr::get(builder.getContext(), name),
        arguments);
}

Value QIRBuilder::constantI64(int64_t value)
{
    return LLVM::ConstantOp::create(builder,
                                    location,
                                    builder.getI64Type(),
                                    builder.getI64IntegerAttr(value));
}

Value QIRBuilder::qubitArray(ResourceManagement resourceManagement,
                             Value base,
                             Value size)
{
    auto type = getQubitArrayType(builder.getContext(), resourceManagement);
    Value array = LLVM::UndefOp::create(builder, location, type);
    array = LLVM::InsertValueOp::create(
        builder, location, array, base, ArrayRef<int64_t>{0});
    return LLVM::InsertValueOp::create(
        builder, location, array, size, ArrayRef<int64_t>{1});
}

Value QIRBuilder::outputLabel(int64_t index)
{
    ModuleOp module = getEnclosingModule(builder);
    std::string name = (llvm::Twine("label") + llvm::Twine(index)).str();
    if (!module.lookupSymbol<LLVM::GlobalOp>(name)) {
        std::string value = (llvm::Twine("result_") + llvm::Twine(index)).str();
        value.push_back('\0');
        Type type = LLVM::LLVMArrayType::get(builder.getI8Type(), value.size());
        OpBuilder::InsertionGuard guard(builder);
        builder.setInsertionPointToStart(module.getBody());
        LLVM::GlobalOp::create(builder,
                               location,
                               type,
                               true,
                               LLVM::Linkage::Internal,
                               name,
                               builder.getStringAttr(value));
    }

    return LLVM::AddressOfOp::create(
        builder,
        location,
        LLVM::LLVMPointerType::get(builder.getContext()),
        name);
}

void QIRBuilder::recordResult(Value result, int64_t outputIndex)
{
    Value label = outputLabel(outputIndex);
    call("__quantum__rt__result_record_output", ValueRange{result, label});
}

Value QIRBuilder::pointerAddress(Value buffer, Value index)
{
    Type pointerType = LLVM::LLVMPointerType::get(builder.getContext());
    return LLVM::GEPOp::create(
        builder, location, pointerType, pointerType, buffer, ValueRange{index});
}

Value QIRBuilder::pointerElement(Value buffer, Value index)
{
    Type pointerType = LLVM::LLVMPointerType::get(builder.getContext());
    Value address = pointerAddress(buffer, index);
    return LLVM::LoadOp::create(builder, location, pointerType, address, 8);
}

void QIRBuilder::storePointerElement(Value value, Value buffer, Value index)
{
    LLVM::StoreOp::create(
        builder, location, value, pointerAddress(buffer, index), 8);
}

Value QIRBuilder::fixedPointerBuffer(int64_t count)
{
    Type pointerType = LLVM::LLVMPointerType::get(builder.getContext());
    Type arrayType = LLVM::LLVMArrayType::get(pointerType, count);
    return LLVM::AllocaOp::create(
        builder, location, pointerType, arrayType, constantI64(1), 8);
}

Value QIRBuilder::dynamicPointerBuffer(Value count)
{
    Type pointerType = LLVM::LLVMPointerType::get(builder.getContext());
    return LLVM::AllocaOp::create(
        builder, location, pointerType, pointerType, count, 8);
}

Value QIRBuilder::measureStaticQubit(Value qubit, int64_t resultId)
{
    Value result = LLVM::IntToPtrOp::create(
        builder,
        location,
        LLVM::LLVMPointerType::get(builder.getContext()),
        constantI64(resultId));
    call("__quantum__qis__mz__body", ValueRange{qubit, result});
    recordResult(result, resultId);
    return call("__quantum__rt__read_result",
                result,
                TypeRange{builder.getI1Type()})
        .getResult();
}

} // namespace mlir::jasp::internal
