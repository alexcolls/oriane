cmake_minimum_required(VERSION 3.15)
project(VideoCropper LANGUAGES CXX)

# Use C++11
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Where you installed your CUDA-enabled FFmpeg
set(FFMPEG_ROOT "$ENV{HOME}/ffmpeg-cuda")

# Make sure pkg-config sees your nv-codec-headers
#   (use $ENV{PKG_CONFIG_PATH}, not ${ENV{PKG_CONFIG_PATH}})
set(ENV{PKG_CONFIG_PATH} "${FFMPEG_ROOT}/lib/pkgconfig:$ENV{PKG_CONFIG_PATH}")

# Find CUDA runtime
find_package(CUDAToolkit REQUIRED)

# Use pkg-config to locate the shared FFmpeg modules
find_package(PkgConfig REQUIRED)
pkg_check_modules(AVFILTER    REQUIRED libavfilter)
pkg_check_modules(AVCODEC     REQUIRED libavcodec)
pkg_check_modules(AVFORMAT    REQUIRED libavformat)
pkg_check_modules(AVUTIL      REQUIRED libavutil)
pkg_check_modules(SWSCALE     REQUIRED libswscale)
pkg_check_modules(SWRESAMPLE  REQUIRED libswresample)

# Include dirs (FFmpeg + CUDA)
include_directories(
  ${AVFILTER_INCLUDE_DIRS}
  ${AVCODEC_INCLUDE_DIRS}
  ${AVFORMAT_INCLUDE_DIRS}
  ${AVUTIL_INCLUDE_DIRS}
  ${SWSCALE_INCLUDE_DIRS}
  ${SWRESAMPLE_INCLUDE_DIRS}
  ${CUDAToolkit_INCLUDE_DIRS}
)

# Library search paths
link_directories(
  ${AVFILTER_LIBRARY_DIRS}
  ${AVCODEC_LIBRARY_DIRS}
  ${AVFORMAT_LIBRARY_DIRS}
  ${AVUTIL_LIBRARY_DIRS}
  ${SWSCALE_LIBRARY_DIRS}
  ${SWRESAMPLE_LIBRARY_DIRS}
)

# Our executable
add_executable(app main.cpp)

# Force your FFmpeg‐CUDA lib dir into the RPATH so at runtime you pick up
# libavfilter.so.11, libavcodec.so.62, etc. from $HOME/ffmpeg-cuda/lib
set_target_properties(app PROPERTIES
  BUILD_WITH_INSTALL_RPATH    TRUE
  INSTALL_RPATH               "${FFMPEG_ROOT}/lib"
  INSTALL_RPATH_USE_LINK_PATH TRUE
)

# Link only the shared libs and CUDA
target_link_libraries(app PRIVATE
  ${AVFILTER_LIBRARIES}
  ${AVCODEC_LIBRARIES}
  ${AVFORMAT_LIBRARIES}
  ${AVUTIL_LIBRARIES}
  ${SWSCALE_LIBRARIES}
  ${SWRESAMPLE_LIBRARIES}
  Threads::Threads
  CUDA::cudart
)
