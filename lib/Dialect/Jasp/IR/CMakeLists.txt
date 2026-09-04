include_directories(
  ${MLIR_INCLUDE_DIRS}
  ${PROJECT_SOURCE_DIR}/include/JaspToQIR/Dialect/Jasp/IR
)

set(LLVM_TARGET_DEFINITIONS
  ${PROJECT_SOURCE_DIR}/include/JaspToQIR/Dialect/Jasp/IR/JaspOps.td
)
mlir_tablegen(JaspOps.h.inc -gen-op-decls)
mlir_tablegen(JaspOps.cpp.inc -gen-op-defs)
mlir_tablegen(JaspOpsTypes.h.inc -gen-typedef-decls -typedefs-dialect=jasp)
mlir_tablegen(JaspOpsTypes.cpp.inc -gen-typedef-defs -typedefs-dialect=jasp)
mlir_tablegen(JaspOpsDialect.h.inc -gen-dialect-decls -dialect=jasp)
mlir_tablegen(JaspOpsDialect.cpp.inc -gen-dialect-defs -dialect=jasp)
add_custom_target(JaspToQIRJaspOpsIncGen DEPENDS ${TABLEGEN_OUTPUT})

add_library(JaspToQIRJaspIR STATIC JaspOps.cpp)
add_dependencies(JaspToQIRJaspIR JaspToQIRJaspOpsIncGen)
target_include_directories(JaspToQIRJaspIR PUBLIC
  ${PROJECT_SOURCE_DIR}/include
  ${CMAKE_CURRENT_BINARY_DIR}
  ${MLIR_INCLUDE_DIRS}
)
mlir_target_link_libraries(JaspToQIRJaspIR PUBLIC MLIRIR)
