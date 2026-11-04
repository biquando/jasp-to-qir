add_library(JaspToQIRQEC STATIC
  codes/Dummy.cpp
  QEC.cpp
  QECCode.cpp
)

target_include_directories(JaspToQIRQEC PUBLIC
  ${PROJECT_SOURCE_DIR}/include
  ${PROJECT_BINARY_DIR}
)
target_include_directories(JaspToQIRQEC PRIVATE ${MLIR_INCLUDE_DIRS})
target_link_libraries(JaspToQIRQEC PUBLIC JaspToQIRJaspIR)
mlir_target_link_libraries(JaspToQIRQEC PUBLIC
  MLIRFuncDialect
  MLIRIR
  MLIRPass
)
