add_library(JaspToQIRFinalizeQIRLLVM STATIC
  FinalizeQIRLLVM.cpp
)

target_include_directories(JaspToQIRFinalizeQIRLLVM PUBLIC
  ${PROJECT_SOURCE_DIR}/include
  ${PROJECT_BINARY_DIR}
)
target_include_directories(JaspToQIRFinalizeQIRLLVM PRIVATE ${MLIR_INCLUDE_DIRS})
mlir_target_link_libraries(JaspToQIRFinalizeQIRLLVM PUBLIC
  MLIRIR
  MLIRLLVMDialect
  MLIRPass
)
