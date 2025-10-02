rm -rf build
mkdir build && cd build

cmake ..
make -j$(nproc)
# g++ main.cpp $(pkg-config --cflags --libs libavformat libavcodec libavfilter libavutil libswscale libswresample) -o app -g

# Verify at link time you see both:
ldd app | grep npp     # should list libnpp*.so from your CUDA install
ldd app | grep avfilter  # should point at libavfilter.so.11 in $HOME/ffmpeg-cuda/lib
