#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "JaspToLLVMInternal.h"
#include "QIRBuilder.h"
#include "llvm/Support/MathExtras.h"
#include "mlir/Dialect/Arith/IR/Arith.h"

using namespace mlir;

namespace mlir::jasp::internal {

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

// Decompositions receive scalarized operands in Jasp order (qubits, then
// parameters). Emit QIR calls in execution order, with angles before qubits.
struct GateDecomposition {
    StringLiteral jaspName;
    unsigned operandCount;
    void (*emit)(ConversionPatternRewriter &, Location, ValueRange);
};

template <bool adjoint>
void emitSqrtX(ConversionPatternRewriter &rewriter, Location loc, ValueRange args)
{
    QIRBuilder qir(rewriter, loc);
    // Qrisp defines sx and its adjoint as Rx(+/- pi/2).
    double angle = (adjoint ? -1 : 1) * llvm::numbers::pi / 2;
    Value parameter = arith::ConstantOp::create(rewriter, loc, rewriter.getF64FloatAttr(angle));
    qir.call("__quantum__qis__rx__body", {parameter, args[0]});
}

void emitU3(ConversionPatternRewriter &rewriter, Location loc, ValueRange args)
{
    QIRBuilder qir(rewriter, loc);
    // U3(theta, phi, lambda) = Rz(phi) Ry(theta) Rz(lambda), up to
    // global phase, which is unobservable for this uncontrolled gate.
    qir.call("__quantum__qis__rz__body", {args[3], args[0]});
    qir.call("__quantum__qis__ry__body", {args[1], args[0]});
    qir.call("__quantum__qis__rz__body", {args[2], args[0]});
}

void emitCY(ConversionPatternRewriter &rewriter, Location loc, ValueRange args)
{
    QIRBuilder qir(rewriter, loc);
    // Y = S X S†; apply both phase gates to the target.
    qir.call("__quantum__qis__s__adj", {args[1]});
    qir.call("__quantum__qis__cnot__body", args);
    qir.call("__quantum__qis__s__body", {args[1]});
}

constexpr GateDecomposition decompositions[] = {
    {"sx", 1, emitSqrtX<false>},
    {"sx_dg", 1, emitSqrtX<true>},
    {"u3", 4, emitU3},
    {"cy", 2, emitCY},
};

const GateDecomposition *findDecomposition(StringRef name)
{
    for (const GateDecomposition &gate : decompositions) {
        if (gate.jaspName == name) {
            return &gate;
        }
    }
    return nullptr;
}

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
        if (operation.getGateType() == "gphase") {
            rewriter.eraseOp(operation);
            return success();
        }

        SmallVector<Value> arguments;
        for (ValueRange values : adaptor.getGateOperands()) {
            arguments.append(values.begin(), values.end());
        }

        if (const auto *decomposition = findDecomposition(operation.getGateType())) {
            if (arguments.size() != decomposition->operandCount) {
                return operation.emitError("incorrect operand count for gate '")
                       << operation.getGateType() << "'";
            }
            decomposition->emit(rewriter, operation.getLoc(), arguments);
            rewriter.eraseOp(operation);
            return success();
        }

        const GateSpec *specification = findGate(operation.getGateType());
        if (!specification) {
            return rewriter.notifyMatchFailure(operation, "unsupported gate");
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
    return name == "gphase"
        || findGate(name) != nullptr
        || findDecomposition(name) != nullptr;
}

void populateQuantumGatePatterns(TypeConverter &converter,
                                 RewritePatternSet &patterns)
{
    patterns.add<LowerQuantumGate>(converter, patterns.getContext());
}

} // namespace mlir::jasp::internal
