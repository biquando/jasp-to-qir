#include "JaspToQIR/Transforms/QEC/QEC.h"

#include "QECCode.h"
#include "llvm/ADT/DenseMap.h"
#include "llvm/ADT/TypeSwitch.h"
#include "llvm/Support/CommandLine.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/OwningOpRef.h"
#include "mlir/IR/SymbolTable.h"

#include <tuple>

namespace {

using namespace mlir;
using jasp_to_qir::qec::Code;

constexpr llvm::StringLiteral helperAttr = "jasp.qec_helper";

template <typename Op>
func::FuncOp createHelper(Op op, FunctionType type, const Code &implementation,
                          StringRef codeName, SymbolTable &symbols)
{
    StringRef name = op->getName().stripDialect();
    if (auto gate = dyn_cast<jasp::QuantumGateOp>(op.getOperation())) {
        name = gate.getGateType();
    }
    OwningOpRef ownedHelper(func::FuncOp::create(
        op.getLoc(), ("__qec_" + codeName + "_" + name).str(), type));
    func::FuncOp helper = ownedHelper.get();
    helper.setPrivate();
    helper->setAttr(helperAttr, UnitAttr::get(op->getContext()));

    Block *entry = helper.addEntryBlock();
    OpBuilder builder = OpBuilder::atBlockEnd(entry);
    auto results = implementation.emit(op, builder, entry->getArguments());
    if (failed(results)) {
        return {};
    }
    func::ReturnOp::create(builder, op.getLoc(), *results);
    symbols.insert(ownedHelper.release());
    return helper;
}

struct QECPass final
    : PassWrapper<QECPass, OperationPass<ModuleOp>> {
    MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(QECPass)

    QECPass() = default;
    QECPass(const QECPass &other) : PassWrapper(other) {}

    llvm::StringRef getArgument() const final { return "qec"; }
    llvm::StringRef getDescription() const final
    {
        return "Replace jasp operations with logical qec operations";
    }

    Option<std::string> code_name{*this, "code",
                                  llvm::cl::desc("QEC code"),
                                  llvm::cl::init("dummy")};

    void getDependentDialects(DialectRegistry &registry) const override
    {
        registry.insert<func::FuncDialect>();
    }

    void runOnOperation() override
    {
        ModuleOp module = getOperation();
        auto code = jasp_to_qir::qec::createCode(code_name.getValue());
        if (!code) {
            module.emitError() << "unsupported QEC code '" << code_name.getValue() << "'";
            signalPassFailure();
            return;
        }

        // Collect source operations before inserting any physical helper bodies.
        SmallVector<Operation *> operations;
        for (auto function : module.getOps<func::FuncOp>()) {
            if (!function->hasAttr(helperAttr)) {
                function.walk([&](Operation *op) {
                    if (op->getName().getDialectNamespace() == jasp::JaspDialect::getDialectNamespace()) {
                        operations.push_back(op);
                    }
                });
            }
        }

        // wrap() replaces jasp operations with logical helper function calls
        using HelperKey = std::tuple<StringAttr, FunctionType, DictionaryAttr>;
        llvm::DenseMap<HelperKey, func::FuncOp> helpers;
        SymbolTable symbols(module);
        auto wrap = [&](auto op) -> LogicalResult {
            OpBuilder builder(op);
            auto type = builder.getFunctionType(op->getOperandTypes(), op->getResultTypes());
            auto key = HelperKey{op->getName().getIdentifier(), type, op->getAttrDictionary()};
            auto &helper = helpers[key];
            if (!helper) {
                helper = createHelper(op, type, *code, code_name.getValue(), symbols);
                if (!helper) {
                    return op.emitError() << "cannot implement operation with QEC code '"
                                          << code_name.getValue() << "'";
                }
            }
            auto call = func::CallOp::create(builder, op->getLoc(), helper, op->getOperands());
            op->replaceAllUsesWith(call.getResults());
            op->erase();
            return success();
        };

        // Call wrap() on (almost) every jasp operation
        //  - create/consume_quantum_kernel: these are still treated as noops
        //  - jasp.parity: this is still unsupported
        for (Operation *op : operations) {
            auto result = llvm::TypeSwitch<Operation *, LogicalResult>(op)
                .Case<jasp::CreateQubitsOp, jasp::DeleteQubitsOp, jasp::GetQubitOp,
                      jasp::GetSizeOp, jasp::SliceOp, jasp::FuseOp, jasp::QuantumGateOp,
                      jasp::MeasureOp, jasp::ResetOp>(wrap)
                .Default([](Operation *) { return success(); });
            if (failed(result)) {
                signalPassFailure();
                return;
            }
        }
    }
};

} // namespace

std::unique_ptr<mlir::Pass> jasp_to_qir::createQECPass()
{
    return std::make_unique<QECPass>();
}
