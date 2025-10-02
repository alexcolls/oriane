#!/usr/bin/env bash
set -e
set -o pipefail

# clean build dir
rm -rf build && mkdir build && cd build

# where you unpacked the NVIDIA Video Codec SDK
SDK_ROOT="../nvidia/Video_Codec_SDK"

# path to the log file (one level up, next to build.sh)
LOG_FILE="../build.log"

# remove any stale log
rm -f "${LOG_FILE}"

echo "=== Building OpenCV-CUDA (logging to ${LOG_FILE}) ==="

# 1) configure  
cmake -G Ninja \
  -DCMAKE_C_COMPILER=/usr/bin/gcc-12 \
  -DCMAKE_CXX_COMPILER=/usr/bin/g++-12 \
  -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/gcc-12 \
  -DWITH_CUDA=ON \
  -DWITH_NVCUVID=ON \
  -DWITH_NVCUVENC=ON \
  -DBUILD_opencv_cudacodec=ON \
  -DOPENCV_EXTRA_MODULES_PATH=../opencv_contrib/modules \
  -DCUDA_ARCH_BIN=75 \
  -DNVCUVID_INCLUDE_DIR:PATH="${SDK_ROOT}/Interface" \
  -DNVCUVID_LIBRARY:FILEPATH="${SDK_ROOT}/Lib/linux/stubs/x86_64/libnvcuvid.so" \
  -DNVCUVENC_INCLUDE_DIR:PATH="${SDK_ROOT}/Interface" \
  -DNVCUVENC_LIBRARY:FILEPATH="${SDK_ROOT}/Lib/linux/stubs/x86_64/libnvidia-encode.so" \
  -DWITH_FFMPEG=ON \
  -DOPENCV_GENERATE_PKGCONFIG=ON \
  -DBUILD_opencv_python3=ON \
  -DPYTHON3_EXECUTABLE="$(which python3)" \
  -DPYTHON3_PACKAGES_PATH="$(python3 -c 'import site; print(site.getsitepackages()[0])')" \
  -DCUDA_NVCC_FLAGS="--allow-unsupported-compiler -std=c++17" \
  -DCMAKE_BUILD_TYPE=Release \
  ../opencv 2>&1 | tee "${LOG_FILE}"

# 2) build
ninja -j"$(nproc)" 2>&1 | tee -a "${LOG_FILE}"

# 3) install
sudo ninja install 2>&1 | tee -a "${LOG_FILE}"

echo "=== Build complete. Logs are in ${LOG_FILE} ==="
