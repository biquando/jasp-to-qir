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
mlir_target_link_libraries(JaspDialect PUBLIC MLIRIR)

add_subdirectory(lib/Conversion/JaspToQIR)
add_subdirectory(lib/Transformation/FinalizeQIRLLVM)

add_executable(jasp-to-qir tools/jasp-to-qir.cpp)
target_link_libraries(jasp-to-qir PRIVATE
  JaspToQIRPass
  FinalizeQIRLLVMPass
  LLVM
)
mlir_target_link_libraries(jasp-to-qir PRIVATE
  MLIROptLib
  MLIRRegisterAllDialects
  MLIRRegisterAllPasses
  MLIRMlirOptMain
  MLIRFuncInlinerExtension
)
