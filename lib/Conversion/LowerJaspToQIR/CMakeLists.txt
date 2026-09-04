add_library(JaspToQIRLowerJaspToQIR STATIC
  LowerJaspToQIR.cpp
  Measurements.cpp
  ModulePreparation.cpp
  QIRBuilder.cpp
  QuantumGates.cpp
  QubitArrayOperations.cpp
  QubitManagement.cpp
  Reset.cpp
  Scalarization.cpp
  TypeConversions.cpp
)

add_dependencies(JaspToQIRLowerJaspToQIR JaspToQIRJaspOpsIncGen)
target_include_directories(JaspToQIRLowerJaspToQIR PUBLIC
  ${PROJECT_SOURCE_DIR}/include
  ${PROJECT_BINARY_DIR}
)
target_include_directories(JaspToQIRLowerJaspToQIR PRIVATE ${MLIR_INCLUDE_DIRS})
target_link_libraries(JaspToQIRLowerJaspToQIR PUBLIC JaspToQIRJaspIR)
mlir_target_link_libraries(JaspToQIRLowerJaspToQIR PUBLIC
  MLIRIR
  MLIRMathDialect
  MLIRArithDialect
  MLIRLLVMDialect
  MLIRSCFDialect
  MLIRPass
  MLIRTransforms
)
