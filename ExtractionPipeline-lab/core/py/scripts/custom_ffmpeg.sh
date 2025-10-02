# Install the basic build tools and dependencies
sudo apt update
sudo apt install -y \
  autoconf automake build-essential cmake git libtool pkg-config \
  yasm texinfo zlib1g-dev libnuma-dev libopus-dev libx264-dev libx265-dev \
  libbz2-dev liblzma-dev

# Install the NVIDIA codec headers
git clone https://github.com/FFmpeg/nv-codec-headers.git
cd nv-codec-headers
make
sudo make install

sudo cp /usr/local/include/ffnvcodec/*.h /usr/local/include/

cd ..

# Clone the FFmpeg source code
git clone https://git.ffmpeg.org/ffmpeg.git src
cd src

# Configure FFmpeg for CUDA
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH}"

./configure \
  --prefix="/usr/local" \
  --pkg-config-flags="--static" \
  --extra-cflags="-I/usr/local/cuda/include" \
  --extra-ldflags="-L/usr/local/cuda/lib64" \
  --extra-libs="-lpthread -lm" \
  --enable-cuda \
  --enable-cuda-nvcc \
  --enable-libnpp \
  --enable-nvdec \
  --enable-nvenc \
  --disable-debug \
  --enable-gpl \
  --enable-cuvid \
  --enable-nonfree

# Build & install FFmpeg
make -j$(nproc)
make install

export PATH="$HOME/ffmpeg-cuda/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg-cuda/lib:$LD_LIBRARY_PATH"

# verify CUDA filters and encoders
ffmpeg -filters   | grep -E 'buffer|hwdownload|hwupload_cuda'
ffmpeg -encoders  | grep nvenc
ldd $(which ffmpeg) | grep libavfilter
