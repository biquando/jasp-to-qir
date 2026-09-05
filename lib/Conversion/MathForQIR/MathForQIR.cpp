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

struct LowerPowf : OpRewritePattern<math::PowFOp> {
    using OpRewritePattern::OpRewritePattern;

    LogicalResult matchAndRewrite(math::PowFOp op,
                                  PatternRewriter &rewriter) const override {
        // Match:
        //   %base = arith.constant 2.0
        auto constantOp = op.getLhs().getDefiningOp<arith::ConstantOp>();
        if (!constantOp) {
            return failure();
        }

        auto floatAttr = dyn_cast<FloatAttr>(constantOp.getValue());
        if (!floatAttr || !floatAttr.getValue().isExactlyValue(2.0)) {
            return failure();
        }

        // Match:
        //   %exp_fp = arith.sitofp %exp
        auto sitofp = op.getRhs().getDefiningOp<arith::SIToFPOp>();
        if (!sitofp) {
            return failure();
        }

        Value exponent = sitofp.getIn();
        auto intType = dyn_cast<IntegerType>(exponent.getType());
        if (!intType) {
            return failure();
        }

        Location loc = op.getLoc();

        // Compute 2^exponent as:
        //   1 << exponent
        Value one = rewriter.create<arith::ConstantIntOp>(loc, 1, intType.getWidth());
        Value shifted = arith::ShLIOp::create(rewriter, loc, one, exponent);

        // Interpret the shifted value as unsigned. This matters for exponent
        // width-1, where the high bit is set.
        Value result = arith::UIToFPOp::create(rewriter, loc, op.getType(), shifted);

        rewriter.replaceOp(op, result);
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
        patterns.add<LowerPowf>(ctx);

        ConversionTarget target(*ctx);
        target.addIllegalOp<math::CtPopOp>();
        target.addIllegalOp<math::PowFOp>();

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
