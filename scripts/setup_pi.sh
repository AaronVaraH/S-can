#!/usr/bin/env bash
# ==============================================================================
# Raspberry Pi Edge-AI Can-Defect Inspector Setup Script
# Target OS: Raspberry Pi OS 64-bit (Debian Bookworm)
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERROR]${NC} $1"; }

INSTALL_DIR="/opt/robert_ai"
SERVICE_USER="${SUDO_USER:-$(whoami)}"

echo "=================================================================="
echo "    Raspberry Pi Industrial Edge-AI Setup & Installation          "
echo "=================================================================="

# 1. Architecture & OS Sanity Check
ARCH=$(uname -m)
log_info "Detected CPU Architecture: ${ARCH}"
if [ "${ARCH}" != "aarch64" ] && [ "${ARCH}" != "armv7l" ]; then
    log_warn "Current architecture is ${ARCH}. Recommended target is Raspberry Pi aarch64 (64-bit)."
fi

# 2. Update System Packages and Install Dependencies
log_info "Updating apt package index..."
sudo apt-get update -y

log_info "Installing system libraries and camera tools..."
sudo apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    v4l-utils \
    libcamera-tools \
    python3-picamera2 \
    gpiod \
    libgpiod-dev \
    logrotate \
    curl

log_ok "System packages installed successfully."

# 3. Create Virtual Environment with System Site Packages (for Picamera2 & libcamera)
log_info "Setting up Python virtual environment in ${INSTALL_DIR}/venv..."
sudo mkdir -p "${INSTALL_DIR}"
sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"

if [ ! -d "${INSTALL_DIR}/venv" ]; then
    python3 -m venv --system-site-packages "${INSTALL_DIR}/venv"
    log_ok "Created virtual environment with system-site-packages enabled."
fi

# 4. Install Python Dependencies
log_info "Installing Python dependencies..."
"${INSTALL_DIR}/venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/venv/bin/pip" install \
    numpy \
    pillow \
    fastapi \
    uvicorn \
    pydantic \
    psutil \
    pyyaml \
    onnxruntime \
    opencv-python-headless \
    pytest \
    httpx

log_ok "Python libraries installed."

# 5. Copy Application Source Code
log_info "Deploying application code to ${INSTALL_DIR}..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sudo cp -r "${SCRIPT_DIR}/config" "${INSTALL_DIR}/"
sudo cp -r "${SCRIPT_DIR}/edge_inspector" "${INSTALL_DIR}/"
sudo cp -r "${SCRIPT_DIR}/models" "${INSTALL_DIR}/"
sudo cp -r "${SCRIPT_DIR}/scripts" "${INSTALL_DIR}/"
sudo cp "${SCRIPT_DIR}/run_inspector.py" "${INSTALL_DIR}/"
sudo mkdir -p "${INSTALL_DIR}/data/inspections"
sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"

# 6. Configure Udev Rules for Camera and GPIO
log_info "Configuring hardware permissions for user ${SERVICE_USER}..."
sudo usermod -aG video,gpio,dialout "${SERVICE_USER}" || true

# 7. Configure Logrotate
log_info "Installing industrial log rotation policy..."
if [ -f "${SCRIPT_DIR}/deploy/logrotate_can_inspector.conf" ]; then
    sudo cp "${SCRIPT_DIR}/deploy/logrotate_can_inspector.conf" /etc/logrotate.d/can_inspector
    sudo chmod 644 /etc/logrotate.d/can_inspector
fi

# 8. Install and Enable Systemd Service
log_info "Installing systemd service unit..."
if [ -f "${SCRIPT_DIR}/deploy/can_inspector.service" ]; then
    # Substitute user and directory
    sed -e "s|User=edgeai|User=${SERVICE_USER}|g" \
        -e "s|/opt/robert_ai|${INSTALL_DIR}|g" \
        "${SCRIPT_DIR}/deploy/can_inspector.service" | sudo tee /etc/systemd/system/can_inspector.service > /dev/null

    sudo systemctl daemon-reload
    sudo systemctl enable can_inspector.service
    log_ok "can_inspector.service enabled for automatic startup."
fi

# 9. Execute Hardware Diagnostics
log_info "Running hardware compatibility diagnostics..."
"${INSTALL_DIR}/venv/bin/python" "${INSTALL_DIR}/scripts/check_hardware.py"

echo "=================================================================="
log_ok "Raspberry Pi Industrial Edge-AI Setup Complete!"
echo "To start the inspection daemon:"
echo "    sudo systemctl start can_inspector.service"
echo "To view live logs:"
echo "    journalctl -u can_inspector.service -f"
echo "To run device benchmarks:"
echo "    ${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/scripts/edge_benchmark.py"
echo "=================================================================="
