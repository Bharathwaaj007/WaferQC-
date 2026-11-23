#!/usr/bin/env bash
# ==============================================================================
# WaferQC Raspberry Pi 5 (8GB) Environment Provisioning Script
# Target OS: Raspberry Pi OS 64-bit (Debian Bookworm) with Active Cooler
# ==============================================================================
set -e

echo "=== [1/5] Updating OS Packages & Toolchain ==="
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git build-essential cmake ninja-build python3-dev python3-pip python3-venv libopenblas-dev libatomic1 htop

echo "=== [2/5] Creating Python Virtual Environment ==="
python3 -m venv ~/waferqc_env
source ~/waferqc_env/bin/activate
pip install --upgrade pip setuptools wheel

echo "=== [3/5] Installing PyTorch & Core Dependencies ==="
# Install ARM64 PyTorch and torchvision wheels
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install opencv-python-headless scipy numpy matplotlib pyyaml rank-bm25 fastapi uvicorn jinja2

echo "=== [4/5] Building ExecuTorch with XNNPACK Backend ==="
cd ~
if [ ! -d "executorch" ]; then
    git clone --depth=1 --branch v0.4.0 https://github.com/pytorch/executorch.git
fi
cd executorch
git submodule update --init --recursive

# Install ExecuTorch Python package
./install_requirements.sh
pip install .

# Build XNNPACK execution runner
cmake -DCMAKE_BUILD_TYPE=Release \
      -DEXECUTORCH_BUILD_XNNPACK=ON \
      -DEXECUTORCH_BUILD_EXTENSION_MODULE=ON \
      -Bbuild-xnnpack
cmake --build build-xnnpack -j4

echo "=== [5/5] Thermal Governor & Core Pinning Setup ==="
# Set CPU scaling governor to performance for deterministic latency benchmarking
sudo cpupower frequency-set -g performance || true

echo "=== WaferQC Pi 5 Setup Complete! ==="
