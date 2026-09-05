#include "JaspToQIR/Dialect/Jasp/IR/JaspOps.h"
#include "JaspToQIR/Conversion/JaspToLLVM/JaspToLLVM.h"
#include "JaspToQIR/Conversion/MathForQIR/MathForQIR.h"
#include "JaspToQIR/Transforms/FinalizeQIRLLVM/FinalizeQIRLLVM.h"
#include "mlir/IR/Dialect.h"
#include "mlir/IR/DialectRegistry.h"
#include "mlir/InitAllDialects.h"
#include "mlir/InitAllPasses.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
#include "mlir/Dialect/Func/Extensions/InlinerExtension.h"


int main(int argc, char **argv) {
  mlir::registerAllPasses();
  mlir::DialectRegistry registry;
  mlir::registerAllDialects(registry);
  mlir::func::registerInlinerExtension(registry);
  registry.insert<jasp::JaspDialect>();
  mlir::registerPass([] { return jasp_to_qir::createJaspToLLVMPass(); });
  mlir::registerPass([] { return jasp_to_qir::createMathForQIRPass(); });
  mlir::registerPass([] { return jasp_to_qir::createFinalizeQIRLLVMPass(); });
  return mlir::asMainReturnCode(
      mlir::MlirOptMain(argc, argv, "Jasp to QIR\n", registry));
}
