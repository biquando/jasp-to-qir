cmake_minimum_required(VERSION 3.20)
project(jasp_to_qir LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(MLIR REQUIRED CONFIG)
list(APPEND CMAKE_MODULE_PATH "${MLIR_CMAKE_DIR}")
include(AddMLIR)
include_directories(${MLIR_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR}/include/Jasp/IR)

set(LLVM_TARGET_DEFINITIONS include/Jasp/IR/JaspOps.td)
mlir_tablegen(JaspOps.h.inc -gen-op-decls)
mlir_tablegen(JaspOps.cpp.inc -gen-op-defs)
mlir_tablegen(JaspOpsTypes.h.inc -gen-typedef-decls -typedefs-dialect=jasp)
mlir_tablegen(JaspOpsTypes.cpp.inc -gen-typedef-defs -typedefs-dialect=jasp)
mlir_tablegen(JaspOpsDialect.h.inc -gen-dialect-decls -dialect=jasp)
mlir_tablegen(JaspOpsDialect.cpp.inc -gen-dialect-defs -dialect=jasp)
add_custom_target(JaspOpsIncGen DEPENDS ${TABLEGEN_OUTPUT})

add_library(JaspDialect STATIC lib/JaspOps.cpp)
add_dependencies(JaspDialect JaspOpsIncGen)
target_include_directories(JaspDialect PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${CMAKE_CURRENT_BINARY_DIR}
  ${MLIR_INCLUDE_DIRS}
)
target_link_libraries(JaspDialect PUBLIC MLIRIR)

add_library(JaspToQIRPass STATIC lib/JaspToQIR.cpp)
add_dependencies(JaspToQIRPass JaspOpsIncGen)
target_include_directories(JaspToQIRPass PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${CMAKE_CURRENT_BINARY_DIR}
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

add_executable(jasp-to-qir tools/jasp-to-qir.cpp)
target_link_libraries(jasp-to-qir PRIVATE
  JaspToQIRPass
  MLIROptLib
  MLIRRegisterAllDialects
  MLIRRegisterAllPasses
  MLIRMlirOptMain
)
