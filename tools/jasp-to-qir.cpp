#include "Jasp/IR/JaspOps.h"
#include "JaspToQIR/JaspToQIR.h"
#include "mlir/IR/Dialect.h"
#include "mlir/IR/DialectRegistry.h"
#include "mlir/InitAllDialects.h"
#include "mlir/InitAllPasses.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"

int main(int argc, char **argv) {
  mlir::registerAllPasses();
  mlir::DialectRegistry registry;
  mlir::registerAllDialects(registry);
  registry.insert<jasp::JaspDialect>();
  mlir::registerPass([] { return mlir::jasp::createJaspToQIRPass(); });
  return mlir::asMainReturnCode(
      mlir::MlirOptMain(argc, argv, "Jasp to QIR\n", registry));
}
