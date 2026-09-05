#include "JaspToQIR/Conversion/MathForQIR/MathForQIR.h"

#include "mlir/Dialect/Math/IR/Math.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Transforms/DialectConversion.h"

using namespace mlir;

namespace {

struct LowerCtpop : OpRewritePattern<math::CtPopOp> {
    using OpRewritePattern::OpRewritePattern;

    LogicalResult matchAndRewrite(math::CtPopOp op, PatternRewriter &rewriter) const override {
        Location loc = op.getLoc();
        Type type = op.getType();

        IntegerType elementType;
        if (auto integerType = dyn_cast<IntegerType>(type)) {
            elementType = integerType;
        } else if (auto shapedType = dyn_cast<ShapedType>(type)) {
            elementType = dyn_cast<IntegerType>(shapedType.getElementType());
            if (!elementType || !shapedType.hasStaticShape()) {
                return rewriter.notifyMatchFailure(
                        op, "requires a statically shaped integer type");
            }
        } else {
            return rewriter.notifyMatchFailure(op, "requires an integer type");
        }

        unsigned width = elementType.getWidth();

        auto makeConstant = [&](const APInt &value) -> Value {
            auto elementAttr = rewriter.getIntegerAttr(elementType, value);

            if (auto shapedType = dyn_cast<ShapedType>(type)) {
                auto attr = DenseElementsAttr::get(shapedType, elementAttr);
                return rewriter.create<arith::ConstantOp>(loc, attr);
            }

            return rewriter.create<arith::ConstantOp>(loc, elementAttr);
        };

        Value value = op.getOperand();

        // Parallel population count. At each step, add the popcounts of adjacent
        // groups of `shift` bits.
        for (unsigned shift = 1; shift < width; shift <<= 1) {
            APInt mask(width, 0);
            for (unsigned bit = 0; bit < width; ++bit) {
                if ((bit & shift) == 0) {
                    mask.setBit(bit);
                }
            }

            Value maskValue = makeConstant(mask);
            Value shiftValue = makeConstant(APInt(width, shift));

            Value lo = rewriter.create<arith::AndIOp>(loc, value, maskValue);
            Value hi = rewriter.create<arith::ShRUIOp>(loc, value, shiftValue);
            hi = rewriter.create<arith::AndIOp>(loc, hi, maskValue);

            value = rewriter.create<arith::AddIOp>(loc, lo, hi);
        }

        rewriter.replaceOp(op, value);
        return success();
    }
};

struct MathForQIRPass final
    : PassWrapper<MathForQIRPass, OperationPass<ModuleOp>> {
    MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(MathForQIRPass)

    StringRef getArgument() const final { return "convert-math-for-qir"; }
    StringRef getDescription() const final {
        return "Lower math operations that would result in unsupported LLVM "
               "operations";
    }

    void runOnOperation() override {
        MLIRContext *ctx = &getContext();

        RewritePatternSet patterns(ctx);
        patterns.add<LowerCtpop>(ctx);
        // patterns.add<LowerPowf>(ctx); TODO:

        ConversionTarget target(*ctx);
        target.addIllegalOp<math::CtPopOp>();
        // target.addIllegalOp<math::PowFOp>(); TODO:

        target.markUnknownOpDynamicallyLegal([](Operation *) { return true; });

        if (failed(applyPartialConversion(getOperation(), target, std::move(patterns)))) {
            signalPassFailure();
        }
    }
};

} // namespace

std::unique_ptr<mlir::Pass> jasp_to_qir::createMathForQIRPass()
{
    return std::make_unique<MathForQIRPass>();
}
