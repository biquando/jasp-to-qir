#include "Jasp/IR/JaspOps.h"
#include "JaspToQIRInternal.h"
#include "QIRBuilder.h"

using namespace mlir;

namespace mlir::jasp::detail {

namespace {

struct GateSpec {
    StringLiteral jaspName;
    StringLiteral qirName;
    bool rotation;
};

constexpr GateSpec supportedGates[] = {
    {"h", "__quantum__qis__h__body", false},
    {"x", "__quantum__qis__x__body", false},
    {"y", "__quantum__qis__y__body", false},
    {"z", "__quantum__qis__z__body", false},
    {"s", "__quantum__qis__s__body", false},
    {"s_dg", "__quantum__qis__s__adj", false},
    {"t", "__quantum__qis__t__body", false},
    {"t_dg", "__quantum__qis__t__adj", false},
    {"rx", "__quantum__qis__rx__body", true},
    {"ry", "__quantum__qis__ry__body", true},
    {"rz", "__quantum__qis__rz__body", true},
    {"p", "__quantum__qis__rz__body", true},
    {"cx", "__quantum__qis__cnot__body", false},
    {"cz", "__quantum__qis__cz__body", false},
};

const GateSpec *findGate(StringRef name)
{
    for (const GateSpec &gate : supportedGates) {
        if (gate.jaspName == name) {
            return &gate;
        }
    }
    return nullptr;
}

struct LowerQuantumGate final : OpConversionPattern<::jasp::QuantumGateOp> {
    using OpConversionPattern::OpConversionPattern;

    LogicalResult
    matchAndRewrite(::jasp::QuantumGateOp operation,
                    OneToNOpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        const GateSpec *specification = findGate(operation.getGateType());
        if (!specification) {
            return rewriter.notifyMatchFailure(operation, "unsupported gate");
        }

        SmallVector<Value> arguments;
        for (ValueRange values : adaptor.getGateOperands()) {
            arguments.append(values.begin(), values.end());
        }

        // Jasp orders rotation operands as (qubit, angle), while QIR uses
        // (angle, qubit).
        if (specification->rotation && arguments.size() == 2) {
            std::swap(arguments[0], arguments[1]);
        }

        QIRBuilder(rewriter, operation.getLoc())
            .call(specification->qirName, arguments);
        rewriter.eraseOp(operation);
        return success();
    }
};

} // namespace

bool isSupportedQuantumGate(StringRef name)
{
    return findGate(name) != nullptr;
}

void populateQuantumGatePatterns(TypeConverter &converter,
                                 RewritePatternSet &patterns)
{
    patterns.add<LowerQuantumGate>(converter, patterns.getContext());
}

} // namespace mlir::jasp::detail
