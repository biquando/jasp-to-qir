add_library(JaspToQIRJaspToLLVM STATIC
  JaspToLLVM.cpp
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

add_dependencies(JaspToQIRJaspToLLVM JaspToQIRJaspOpsIncGen)
target_include_directories(JaspToQIRJaspToLLVM PUBLIC
  ${PROJECT_SOURCE_DIR}/include
  ${PROJECT_BINARY_DIR}
)
target_include_directories(JaspToQIRJaspToLLVM PRIVATE ${MLIR_INCLUDE_DIRS})
target_link_libraries(JaspToQIRJaspToLLVM PUBLIC JaspToQIRJaspIR)
mlir_target_link_libraries(JaspToQIRJaspToLLVM PUBLIC
  MLIRIR
  MLIRMathDialect
  MLIRArithDialect
  MLIRLLVMDialect
  MLIRSCFDialect
  MLIRPass
  MLIRTransforms
)
