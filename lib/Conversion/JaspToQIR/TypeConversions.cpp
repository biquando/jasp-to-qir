#include "Jasp/IR/JaspOps.h"
#include "JaspToQIRInternal.h"
#include "QIRBuilder.h"
#include "mlir/Dialect/LLVMIR/LLVMDialect.h"
#include "mlir/IR/BuiltinTypes.h"

using namespace mlir;

namespace mlir::jasp::detail {

std::unique_ptr<TypeConverter>
createJaspToQIRTypeConverter(MLIRContext &context,
                             const JaspToQIROptions &options)
{
    auto converter = std::make_unique<TypeConverter>();

    converter->addConversion([](Type type) { return type; });

    converter->addConversion([](RankedTensorType type) -> std::optional<Type> {
        if (type.getRank() == 0
            && (type.getElementType().isInteger()
                || type.getElementType().isF64()))
        {
            return type.getElementType();
        }
        return std::nullopt;
    });

    converter->addConversion(
        [](::jasp::QuantumStateType, SmallVectorImpl<Type> &) -> LogicalResult {
            return success();
        });

    converter->addConversion([&context](::jasp::QubitType) -> Type {
        return LLVM::LLVMPointerType::get(&context);
    });

    ResourceManagement resourceManagement = options.resourceManagement;
    converter->addConversion(
        [&context, resourceManagement](::jasp::QubitArrayType) -> Type {
            return QIRBuilder::getQubitArrayType(&context, resourceManagement);
        });

    return converter;
}

} // namespace mlir::jasp::detail
