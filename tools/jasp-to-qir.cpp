#include "JaspToQIR/JaspToQIR.h"
#include "mlir/IR/Dialect.h"
#include "mlir/IR/DialectRegistry.h"
#include "mlir/InitAllDialects.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"

namespace {

class JaspDialect final : public mlir::Dialect {
public:
  static llvm::StringRef getDialectNamespace() { return "jasp"; }

  explicit JaspDialect(mlir::MLIRContext *context)
      : Dialect(getDialectNamespace(), context,
                mlir::TypeID::get<JaspDialect>()) {
    allowUnknownOperations();
  }
};

} // namespace

int main(int argc, char **argv) {
  mlir::DialectRegistry registry;
  mlir::registerAllDialects(registry);
  registry.insert<JaspDialect>();
  mlir::registerPass([] { return mlir::jasp::createJaspToQIRPass(); });
  return mlir::asMainReturnCode(
      mlir::MlirOptMain(argc, argv, "Jasp to QIR\n", registry));
}
