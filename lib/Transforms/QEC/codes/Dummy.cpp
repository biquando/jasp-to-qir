#include "../QECCode.h"

namespace jasp_to_qir::qec {
namespace {

using namespace mlir;

HelperResults emitPhysical(Operation *source, OpBuilder &builder, ValueRange args)
{
    Operation *physical = builder.clone(*source);
    // Map by position so repeated source operands still get separate parameters.
    physical->setOperands(args);
    return llvm::to_vector(ValueRange(physical->getResults()));
}

class Dummy final : public Code {
public:
    HelperResults emit(jasp::CreateQubitsOp op, OpBuilder &b, ValueRange args) const override
    {
        return emitPhysical(op, b, args);
    }

    HelperResults emit(jasp::DeleteQubitsOp op, OpBuilder &b, ValueRange args) const override
    {
        return emitPhysical(op, b, args);
    }

    HelperResults emit(jasp::GetQubitOp op, OpBuilder &b, ValueRange args) const override
    {
        return emitPhysical(op, b, args);
    }

    HelperResults emit(jasp::GetSizeOp op, OpBuilder &b, ValueRange args) const override
    {
        return emitPhysical(op, b, args);
    }

    HelperResults emit(jasp::SliceOp op, OpBuilder &b, ValueRange args) const override
    {
        return emitPhysical(op, b, args);
    }

    HelperResults emit(jasp::FuseOp op, OpBuilder &b, ValueRange args) const override
    {
        return emitPhysical(op, b, args);
    }

    HelperResults emit(jasp::QuantumGateOp op, OpBuilder &b, ValueRange args) const override
    {
        return emitPhysical(op, b, args);
    }

    HelperResults emit(jasp::MeasureOp op, OpBuilder &b, ValueRange args) const override
    {
        return emitPhysical(op, b, args);
    }

    HelperResults emit(jasp::ResetOp op, OpBuilder &b, ValueRange args) const override
    {
        return emitPhysical(op, b, args);
    }
};

} // namespace

std::unique_ptr<Code> createDummyCode()
{
    return std::make_unique<Dummy>();
}

} // namespace jasp_to_qir::qec
