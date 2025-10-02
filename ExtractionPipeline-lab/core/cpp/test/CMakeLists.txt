# CMake minimum version
cmake_minimum_required(VERSION 3.15)

# Project name and C++ standard
project(VideoCropper LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Find CUDAToolkit (modern way)
# This will locate CUDA and provide variables like CUDAToolkit_INCLUDE_DIRS and CUDAToolkit_LIBRARIES
# It also creates imported targets like CUDA::cudart
find_package(CUDAToolkit REQUIRED)

# Find FFmpeg libraries using PkgConfig
find_package(PkgConfig REQUIRED)
pkg_check_modules(AVCODEC REQUIRED libavcodec)
pkg_check_modules(AVFORMAT REQUIRED libavformat)
pkg_check_modules(AVUTIL REQUIRED libavutil)
pkg_check_modules(SWSCALE REQUIRED libswscale)

# Add executable
# Syntax: add_executable(<target_name> <source1> [source2 ...])
# The target_name should be a simple name, e.g., video_cropper_app
add_executable(app main.cpp)

# Link FFmpeg libraries
target_link_libraries(app
    PRIVATE
    ${AVCODEC_LIBRARIES}
    ${AVFORMAT_LIBRARIES}
    ${AVUTIL_LIBRARIES}
    ${SWSCALE_LIBRARIES}
)

# Link CUDA libraries
# With find_package(CUDAToolkit), you can link against imported targets like CUDA::cudart
# FFmpeg, if built with --enable-cuda-nvcc, might handle some CUDA runtime linking itself.
# However, explicitly linking CUDA::cudart is a good practice if your code (or FFmpeg's usage) needs it.
target_link_libraries(app PRIVATE CUDA::cudart) # Link the CUDA runtime

# Include directories
target_include_directories(app
    PRIVATE
    ${AVCODEC_INCLUDE_DIRS}
    ${AVFORMAT_INCLUDE_DIRS}
    ${AVUTIL_INCLUDE_DIRS}
    ${SWSCALE_INCLUDE_DIRS}
    ${CUDAToolkit_INCLUDE_DIRS} # Include CUDA headers
)

# Print paths for debugging (optional)
message(STATUS "AVCODEC_INCLUDE_DIRS: ${AVCODEC_INCLUDE_DIRS}")
message(STATUS "AVCODEC_LIBRARIES: ${AVCODEC_LIBRARIES}")
message(STATUS "CUDAToolkit_INCLUDE_DIRS: ${CUDAToolkit_INCLUDE_DIRS}")
message(STATUS "CUDAToolkit_LIBRARIES: ${CUDAToolkit_LIBRARIES}") # This will list CUDA libraries like cudart, etc.
message(STATUS "CUDA Version: ${CUDAToolkit_VERSION}")
