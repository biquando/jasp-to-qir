cmake_minimum_required(VERSION 3.20)
project(JaspToQIR LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(MLIR REQUIRED CONFIG)
if(NOT LLVM_VERSION_MAJOR EQUAL 21)
  message(FATAL_ERROR "LLVM 21 required, found LLVM ${LLVM_PACKAGE_VERSION}")
endif()
message(STATUS "Found MLIR at: ${MLIR_DIR}")
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Found LLVM at: ${LLVM_DIR}")

# Do not mix the MLIR component archives with the aggregate MLIR shared
# library.  Some packaged MLIR targets (notably MLIRMlirOptMain) depend on the
# shared library, so mixing them gives MLIR two copies of process-global state
# and can crash while parsing attributes.
if(TARGET MLIR)
  set(MLIR_LINK_MLIR_DYLIB ON)
endif()

list(APPEND CMAKE_MODULE_PATH "${MLIR_CMAKE_DIR}")
include(AddMLIR)

add_subdirectory(lib/Dialect/Jasp/IR)
add_subdirectory(lib/Conversion/LowerJaspToQIR)
add_subdirectory(lib/Conversion/MathForQIR)
add_subdirectory(lib/Transforms/FinalizeQIRLLVM)

add_executable(jasp-to-qir tools/jasp-to-qir.cpp)
target_link_libraries(jasp-to-qir PRIVATE
  JaspToQIRLowerJaspToQIR
  JaspToQIRMathForQIR
  JaspToQIRFinalizeQIRLLVM
  LLVM
)
mlir_target_link_libraries(jasp-to-qir PRIVATE
  MLIROptLib
  MLIRRegisterAllDialects
  MLIRRegisterAllPasses
  MLIRMlirOptMain
  MLIRFuncInlinerExtension
)
