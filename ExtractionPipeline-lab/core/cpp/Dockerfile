# Use NVIDIA’s CUDA base image with development tools
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

# Hint to nvidia-container-runtime what to expose
LABEL com.nvidia.volumes.needed="nvidia_driver"
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

# Ensure CUDA libs are on the loader’s path
ENV LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/cuda/extras/CUPTI/lib64:${LD_LIBRARY_PATH}
ENV PATH=/usr/local/cuda/bin:${PATH}

# ---- System & Build Dependencies ----
# Python, pip, build tools, and FFmpeg build dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 python3-pip python3-setuptools \
    autoconf automake build-essential cmake libtool pkg-config \
    yasm nasm texinfo zlib1g-dev libnuma-dev libopus-dev libx264-dev libx265-dev \
    libbz2-dev liblzma-dev git wget pkg-config libvpx-dev libfdk-aac-dev ninja-build \
  && rm -rf /var/lib/apt/lists/*

# ---- Build FFmpeg from source with NVIDIA NVENC/CUVID ----
RUN mkdir -p /opt/ffmpeg_sources && cd /opt/ffmpeg_sources \
    # Install nv-codec-headers for NVENC
    && git clone --depth 1 https://github.com/FFmpeg/nv-codec-headers.git \
    && cd nv-codec-headers && make && make install \
    # Clone FFmpeg
    && cd /opt/ffmpeg_sources \
    && git clone --depth 1 https://git.ffmpeg.org/ffmpeg.git ffmpeg \
    && cd ffmpeg \
    # Configure with CUDA/NVENC support
    && PKG_CONFIG_PATH="/usr/local/lib/pkgconfig" ./configure \
        --prefix="/usr/local" \
        --pkg-config-flags="--static" \
        --extra-cflags="-I/usr/local/cuda/include" \
        --extra-ldflags="-L/usr/local/cuda/lib64/stubs -L/usr/local/cuda/lib64 -L/usr/local/nvidia/lib64" \
        --extra-libs="-lpthread -lm" \
        --enable-gpl \
        --enable-nonfree \
        --enable-cuda \
        --enable-cuvid \
        --enable-nvenc \
        --enable-libnpp \
        --enable-libx264 \
        --enable-libx265 \
        --enable-libvpx \
        --enable-libfdk-aac \
    && make -j$(nproc) \
    && make install \
    && hash -r

# ---- Python Dependencies ----
WORKDIR /tmp
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# ---- Application Code ----
WORKDIR /app
COPY crop_n_frame.py ./
COPY entrypoint.py   ./

# Keep logs unbuffered
ENV PYTHONUNBUFFERED=1
# Ensure custom-built ffmpeg in /usr/local/bin is picked up
ENV PATH=/usr/local/bin:${PATH}

ENTRYPOINT ["bash", "entrypoint"]
