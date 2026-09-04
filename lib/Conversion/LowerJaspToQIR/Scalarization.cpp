#include "LowerJaspToQIRInternal.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Tensor/IR/Tensor.h"

using namespace mlir;

namespace mlir::jasp::internal {

namespace {

/// Converts an arith.constant holding a rank-zero tensor into a scalar
/// arith.constant.
struct ScalarConstant final : OpConversionPattern<arith::ConstantOp> {
    using OpConversionPattern::OpConversionPattern;

    LogicalResult
    matchAndRewrite(arith::ConstantOp operation,
                    OpAdaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        auto tensor = dyn_cast<RankedTensorType>(operation.getType());
        auto dense = dyn_cast<DenseElementsAttr>(operation.getValue());
        if (!tensor || tensor.getRank() != 0 || !dense) {
            return failure();
        }

        rewriter.replaceOpWithNewOp<arith::ConstantOp>(
            operation,
            tensor.getElementType(),
            dense.getSplatValue<TypedAttr>());
        return success();
    }
};

/// Replaces extraction from a rank-zero tensor with its converted scalar.
struct ScalarExtract final : OpConversionPattern<tensor::ExtractOp> {
    using OpConversionPattern::OpConversionPattern;

    LogicalResult
    matchAndRewrite(tensor::ExtractOp operation,
                    OpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        auto tensor =
            dyn_cast<RankedTensorType>(operation.getTensor().getType());
        if (!tensor || tensor.getRank() != 0 || !operation.getIndices().empty())
        {
            return failure();
        }

        rewriter.replaceOp(operation, adaptor.getTensor());
        return success();
    }
};

/// Replaces creation of a rank-zero tensor with its converted scalar element.
struct ScalarFromElements final : OpConversionPattern<tensor::FromElementsOp> {
    using OpConversionPattern::OpConversionPattern;

    LogicalResult
    matchAndRewrite(tensor::FromElementsOp operation,
                    OpAdaptor adaptor,
                    ConversionPatternRewriter &rewriter) const override
    {
        auto tensor = dyn_cast<RankedTensorType>(operation.getType());
        if (!tensor || tensor.getRank() != 0
            || adaptor.getElements().size() != 1)
        {
            return failure();
        }

        rewriter.replaceOp(operation, adaptor.getElements().front());
        return success();
    }
};

} // namespace

void populateScalarizationPatterns(TypeConverter &converter,
                                   RewritePatternSet &patterns)
{
    patterns.add<ScalarConstant, ScalarExtract, ScalarFromElements>(
        converter, patterns.getContext());
}

} // namespace mlir::jasp::internal
