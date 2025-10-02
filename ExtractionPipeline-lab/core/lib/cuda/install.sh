# Download CUDA
wget https://developer.download.nvidia.com/compute/cuda/12.4.1/local_installers/cuda_12.4.1_550.54.15_linux.run

# Install CUDA
sudo sh cuda_12.4.1_550.54.15_linux.run --toolkit --toolkitpath=/usr/local/cuda-12.4 --no-opengl-libs

# Add CUDA to PATH
export PATH="/usr/local/cuda-12.4/bin:$PATH"

# Add CUDA to LD_LIBRARY_PATH
export LD_LIBRARY_PATH="/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH"

# Verify CUDA compiler installation
nvcc --version

# Verify NVIDIA Driver installation
nvidia-smi

# Verify CUDA installation
nvidia-cuda-mps-control -d

# Verify CUDA installation
nvidia-cuda-mps-control -i
