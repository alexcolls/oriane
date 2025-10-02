g++ crop_n_frame.cpp -o crop_n_frame \
       `pkg-config --cflags --libs opencv4` \
       -std=c++17 -pthread -O2
