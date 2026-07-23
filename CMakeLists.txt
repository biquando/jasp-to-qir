cmake_minimum_required(VERSION 3.20)
project(jasp_to_qir LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(MLIR REQUIRED CONFIG)

add_library(JaspToQIRPass STATIC lib/JaspToQIR.cpp)
target_include_directories(JaspToQIRPass PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_include_directories(JaspToQIRPass PRIVATE ${MLIR_INCLUDE_DIRS})
target_link_libraries(JaspToQIRPass PUBLIC
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
  MLIRMlirOptMain
)
