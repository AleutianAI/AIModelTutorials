#!/bin/bash

# Script to install Podman from source with GPU support on Linux Mint
# Based on: https://podman.io/docs/installation

set -e # Exit on error

# Update package lists and install basic dependencies
sudo apt update
sudo apt install -y software-properties-common golang

# Install Podman build dependencies
sudo apt-get install -y \
    btrfs-progs \
    gcc \
    git \
    golang-go \
    go-md2man \
    iptables \
    libassuan-dev \
    libbtrfs-dev \
    libc6-dev \
    libdevmapper-dev \
    libglib2.0-dev \
    libgpgme-dev \
    libgpg-error-dev \
    libprotobuf-dev \
    libprotobuf-c-dev \
    libseccomp-dev \
    libselinux1-dev \
    libsystemd-dev \
    make \
    netavark \
    passt \
    pkg-config \
    runc \
    uidmap

# Install conmon
echo "Installing conmon..."
git clone https://github.com/containers/conmon
cd conmon
export GOCACHE="$(mktemp -d)"
make
sudo make install

# Install runc
echo "Installing runc..."
export GOPATH="$HOME/go"
mkdir -p "$GOPATH/src/github.com/opencontainers"
git clone https://github.com/opencontainers/runc.git "$GOPATH/src/github.com/opencontainers/runc"
cd "$GOPATH/src/github.com/opencontainers/runc"
make BUILDTAGS="selinux seccomp"
sudo cp runc /usr/bin/runc

# Add container configurations
echo "Adding container configurations..."
sudo mkdir -p /etc/containers
sudo curl -L -o /etc/containers/registries.conf https://raw.githubusercontent.com/containers/image/main/registries.conf
sudo curl -L -o /etc/containers/policy.json https://raw.githubusercontent.com/containers/image/main/default-policy.json

# Install apparmor
echo "Installing apparmor..."
sudo apt install -y libapparmor-dev

# Install Podman from source
echo "Installing Podman from source..."
cd "$HOME"
git clone https://github.com/containers/podman/
cd podman
make BUILDTAGS="selinux seccomp apparmor" PREFIX=/usr
sudo env PATH="$PATH" make install PREFIX=/usr

# Verify Podman installation
echo "Verifying Podman installation..."
podman --version

echo "Podman installation complete."

# Adding the podman community repository for future updates.
echo "Adding the Podman community repository for future updates."
. /etc/os-release
echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/x$ID_$VERSION_ID/ /" | sudo tee /etc/apt/sources.list.d/devel--kubic--libcontainers--stable.list
curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/x$ID_$VERSION_ID/Release.key | sudo apt-key add -
sudo apt update

# Install NVIDIA Container Toolkit
echo "Installing NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt-get install -y nvidia-container-toolkit

# Generate CDI configuration and list CDI devices
echo "Generating CDI configuration and listing CDI devices..."
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
nvidia-ctk cdi list

echo "NVIDIA Container Toolkit installation complete."
echo "Use podman run --gpus all to run containers using your NVIDIA GPU."