#!/usr/bin/env bash
set -e

echo "==> 1. Remove broken NVIDIA sources"
sudo rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list \
            /etc/apt/sources.list.d/cuda*.list

echo "==> 2. Add NVIDIA key & correct repo (stable/ubuntu22.04)"
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /etc/apt/keyrings/nvidia-container-toolkit.gpg

ARCH=$(dpkg --print-architecture)        # amd64
sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null <<EOF
deb [signed-by=/etc/apt/keyrings/nvidia-container-toolkit.gpg] \
https://nvidia.github.io/libnvidia-container/stable/ubuntu22.04/$ARCH/ /
EOF

echo "==> 3. Update & install toolkit"
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

echo "==> 4. Wire the runtime into Docker"
sudo nvidia-ctk runtime configure --runtime=docker --set-as-default

echo "==> 5. Restart Docker"
sudo systemctl restart docker
echo "✅  NVIDIA Container Toolkit installed & runtime registered"


echo "==> 6. Verify installation"
# 1. Docker must list the 'nvidia' runtime
docker info --format '{{json .Runtimes}}' | jq .
# → { "io.containerd.runc.v2": {}, "nvidia": {} }
# 2. GPU visible *inside* a container
docker run --rm --gpus all \
  nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
