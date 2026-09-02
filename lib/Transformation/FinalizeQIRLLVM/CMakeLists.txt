add_library(FinalizeQIRLLVMPass STATIC
  FinalizeQIRLLVM.cpp
)

target_include_directories(FinalizeQIRLLVMPass PUBLIC
  ${CMAKE_SOURCE_DIR}/include
  ${CMAKE_BINARY_DIR}
)
target_include_directories(FinalizeQIRLLVMPass PRIVATE ${MLIR_INCLUDE_DIRS})
mlir_target_link_libraries(FinalizeQIRLLVMPass PUBLIC
  MLIRIR
  MLIRLLVMDialect
  MLIRPass
)
