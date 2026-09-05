add_library(JaspToQIRMathForQIR STATIC
  MathForQIR.cpp
)

target_include_directories(JaspToQIRMathForQIR PUBLIC
  ${PROJECT_SOURCE_DIR}/include
  ${PROJECT_BINARY_DIR}
)
target_include_directories(JaspToQIRMathForQIR PRIVATE ${MLIR_INCLUDE_DIRS})
mlir_target_link_libraries(JaspToQIRMathForQIR PUBLIC
  MLIRIR
  MLIRMathDialect
  MLIRArithDialect
  MLIRPass
  MLIRTransforms
)
