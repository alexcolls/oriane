# ------------------------------------------------------------ #
# Oriane Visual Extraction Pipeline - FastAPI + GPU Processing
# ------------------------------------------------------------ #

FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 as base

LABEL maintainer="alex@oriane.xyz"
LABEL description="Oriane Visual Extraction Pipeline - FastAPI + GPU Processing"
LABEL com.nvidia.volumes.needed="nvidia_driver"

ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video
ENV LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64:${LD_LIBRARY_PATH}
ENV PATH=/usr/local/cuda/bin:${PATH}

# System deps, OpenCV + libGL fix included
RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates curl wget git python3 python3-pip python3-setuptools python3-dev \
  build-essential cmake libtool pkg-config yasm nasm texinfo ninja-build \
  zlib1g-dev libnuma-dev libbz2-dev liblzma-dev \
  libopus-dev libx264-dev libx265-dev libvpx-dev libfdk-aac-dev \
  libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 libgl1 \
  libgstreamer1.0-0 libgstreamer-plugins-base1.0-0 \
  htop nano vim && \
  rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3 /usr/bin/python

# ----------------- FFmpeg Build -----------------
FROM base as ffmpeg-builder

RUN mkdir -p /opt/ffmpeg_sources && cd /opt/ffmpeg_sources && \
  git clone --depth 1 https://github.com/FFmpeg/nv-codec-headers.git && \
  cd nv-codec-headers && make && make install

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
  --enable-libnpp --enable-libx264 --enable-libx265 --enable-libvpx --enable-libfdk-aac && \
  make -j"$(nproc)" && make install && hash -r

RUN rm -rf /usr/local/cuda/lib64/stubs

# ----------------- Final Stage -----------------
FROM base as application

COPY --from=ffmpeg-builder /usr/local/bin/ff* /usr/local/bin/
COPY --from=ffmpeg-builder /usr/local/lib/pkgconfig /usr/local/lib/pkgconfig
COPY --from=ffmpeg-builder /usr/local/include /usr/local/include
COPY --from=ffmpeg-builder /usr/local/lib/lib* /usr/local/lib/

RUN ldconfig

WORKDIR /app

# Copy full api folder keeping structure
COPY api/search/ /app/api/
COPY api/search/.env /app/api/.env

# Install requirements from correct location
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
  python -m pip install --no-cache-dir -r /app/api/requirements.txt

# Copy rest of source code
COPY core/py/pipeline/src /app/core/py/pipeline/src/
COPY core/py/pipeline/config /app/core/py/pipeline/config/
COPY core/py/pipeline/entrypoint.py /app/core/py/pipeline/
COPY core/py/pipeline/models /app/core/py/pipeline/models/

ENV PYTHONPATH=/app:/app/api:/app/core/py/pipeline
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/temp /app/output /app/logs /app/models && chmod -R 755 /app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["uvicorn"]
CMD ["api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
