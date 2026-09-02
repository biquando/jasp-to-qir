add_library(JaspToQIRPass STATIC
  JaspToQIR.cpp
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

add_dependencies(JaspToQIRPass JaspOpsIncGen)
target_include_directories(JaspToQIRPass PUBLIC
  ${CMAKE_SOURCE_DIR}/include
  ${CMAKE_BINARY_DIR}
)
target_include_directories(JaspToQIRPass PRIVATE ${MLIR_INCLUDE_DIRS})
target_link_libraries(JaspToQIRPass PUBLIC
  JaspDialect
  MLIRIR
  MLIRArithDialect
  MLIRLLVMDialect
  MLIRSCFDialect
  MLIRPass
  MLIRTransforms
)
