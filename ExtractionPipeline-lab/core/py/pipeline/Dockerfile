# ------------------------------------------------------------ #
#  Base: CUDA 12.4.1 with build tool-chain
# ------------------------------------------------------------ #
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

LABEL maintainer="alex@oriane.xyz"
LABEL com.nvidia.volumes.needed="nvidia_driver"

ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

# CUDA paths
ENV LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:\
    /usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64:${LD_LIBRARY_PATH}
ENV PATH=/usr/local/cuda/bin:${PATH}

# ------------------------------------------------------------ #
#  System & build dependencies (+ root CA bundle)
# ------------------------------------------------------------ #
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 python3-pip python3-setuptools \
    autoconf automake build-essential cmake libtool pkg-config \
    yasm nasm texinfo zlib1g-dev libnuma-dev \
    libopus-dev libx264-dev libx265-dev libbz2-dev liblzma-dev \
    libvpx-dev libfdk-aac-dev ninja-build git wget && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------ #
#  Trust the custom AWS-RDS / Qdrant CA
# ------------------------------------------------------------ #
#   Place cert/aws-rds-global.pem next to this Dockerfile
COPY cert/aws-rds-global.pem /usr/local/share/ca-certificates/aws-rds-global.crt
RUN update-ca-certificates

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=$SSL_CERT_FILE

# ------------------------------------------------------------ #
#  Build nv-codec-headers (for CUDA decode/encode in FFmpeg)
# ------------------------------------------------------------ #
RUN mkdir -p /opt/ffmpeg_sources && cd /opt/ffmpeg_sources && \
    git clone --depth 1 https://github.com/FFmpeg/nv-codec-headers.git && \
    cd nv-codec-headers && make && make install

# ------------------------------------------------------------ #
#  Build FFmpeg with CUDA, NVENC, CUVID, NPP
# ------------------------------------------------------------ #
RUN cd /opt/ffmpeg_sources && \
    git clone --depth 1 https://github.com/FFmpeg/FFmpeg.git ffmpeg && \
    cd ffmpeg && \
    PKG_CONFIG_PATH="/usr/local/lib/pkgconfig" ./configure \
    --prefix="/usr/local" \
    --pkg-config-flags="--static" \
    --extra-cflags="-I/usr/local/cuda/include" \
    --extra-ldflags="-L/usr/local/cuda/lib64/stubs -L/usr/local/cuda/lib64 -L/usr/local/nvidia/lib64" \
    --extra-libs="-lpthread -lm" \
    --enable-gpl --enable-nonfree \
    --enable-cuda --enable-cuda-nvcc --enable-cuvid --enable-nvenc \
    --enable-libnpp \
    --enable-libx264 --enable-libx265 \
    --enable-libvpx --enable-libfdk-aac && \
    make -j"$(nproc)" && \
    make install && \
    hash -r

#  Remove the stub libs so runtime picks the real ones
RUN rm -rf /usr/local/cuda/lib64/stubs

# ------------------------------------------------------------ #
#  Python dependencies
# ------------------------------------------------------------ #
WORKDIR /tmp
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------ #
#  Application code
# ------------------------------------------------------------ #
WORKDIR /app
COPY models ./models
COPY crop_n_frame.py .
COPY frames_embeddings.py .
COPY entrypoint.py .

ENV PYTHONUNBUFFERED=1
ENV PATH=/usr/local/bin:${PATH}

ENTRYPOINT ["python3", "entrypoint.py"]
