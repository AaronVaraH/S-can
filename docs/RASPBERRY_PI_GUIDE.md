# Raspberry Pi Edge-AI Industrial Can-Defect Inspection System: Deployment Guide

## 1. System Overview
This system is an industrial edge computer vision and document assistance platform engineered specifically for **Raspberry Pi 4 Model B, Raspberry Pi 5, and Raspberry Pi Compute Module 4 (CM4)**. It inspects cans moving along high-speed conveyors for dents, scratches, rim deformations, pinholes, and double seam flaws.

### Key Architectural Characteristics
- **Lightweight CPU / Accelerator Inference**: Runs under **ONNX Runtime (with ARM NEON SIMD vectorization)** or **TensorFlow Lite (XNNPACK)**, with native support for the **Raspberry Pi AI HAT+ (Hailo-8 / Hailo-8L)**.
- **Fail-Safe Gate**: Blurry frames, overexposed glare, model loading faults, or timing deadlines trigger a **REVIEW** state; unverified cans are never accepted.
- **Non-Blocking Architecture**: Bounded queue with memory guard and background async processing to prevent UI or acquisition freeze.
- **100% Offline RAG**: Local factory documentation indexer and BM25 retriever requiring zero internet connection and negligible RAM (< 10 MB).
- **Physical Separation of Concerns**: Training is strictly offloaded to workstations or GPU servers; the Raspberry Pi exclusively handles inference, telemetry, and reject actuation.

---

## 2. Hardware Bill of Materials (BOM)
1. **Compute Module**:
   - *Recommended*: **Raspberry Pi 5 (4GB or 8GB RAM)** with active cooler fan.
   - *Supported*: **Raspberry Pi 4 Model B (4GB or 8GB RAM)** with heatsink and fan.
2. **Camera Hardware**:
   - Official **Raspberry Pi Camera Module 3** or **Global Shutter Camera** (C-mount, IMX296 sensor, 1.58 MP, global shutter eliminates motion blur at high belt speeds).
   - Alternatively: Industrial USB3 / UVC camera (e.g. Basler, FLIR, or standard V4L2 USB camera).
3. **Optics & Illumination**:
   - C-Mount industrial 12mm or 16mm manual lockable focus lens.
   - **Diffuse Dome Illuminator** or **Darkfield Ring Light** (24V industrial supply) to suppress specular glare from shiny aluminum / tinplate can bodies.
4. **Reject Mechanism**:
   - 24V DC pneumatic solenoid blow-off valve.
   - Optocoupled solid-state relay module (3.3V GPIO trigger to 24V solenoid).
   - Clean industrial compressed air regulator (5.5 to 6.5 bar).
5. **Storage**:
   - High-endurance Class 10 / A2 MicroSD card (32GB+) or PCIe NVMe M.2 SSD HAT for Raspberry Pi 5.

---

## 3. Operating System Setup & Pre-requisites
Install **Raspberry Pi OS 64-bit (Debian Bookworm)**.

### Boot Configuration (`/boot/firmware/config.txt`)
Ensure the camera and PCIe interfaces are enabled:
```ini
# Enable camera interface
camera_auto_detect=1

# Enable PCIe Gen 3 for Raspberry Pi 5 (if using Hailo AI HAT+ or NVMe)
dtparam=pciex1
dtparam=pciex1_gen=3

# Prevent GPU memory starvation
gpu_mem=128
```

---

## 4. One-Step Automated Installation
Run the production installation script:
```bash
sudo bash scripts/setup_pi.sh
```

The script will:
1. Verify 64-bit ARM architecture.
2. Install `python3-picamera2`, `libcamera-tools`, `gpiod`, and required system libraries.
3. Create a dedicated virtual environment with access to system packages:
   ```bash
   python3 -m venv --system-site-packages /opt/robert_ai/venv
   ```
4. Install `onnxruntime`, `opencv-python-headless`, `fastapi`, and dependencies.
5. Install and enable the systemd service `/etc/systemd/system/can_inspector.service`.

---

## 5. Wiring and GPIO Interlocks
Connect the optocoupled relay controlling the reject pneumatic valve to Raspberry Pi header:

| Signal | Raspberry Pi Pin | Function |
|---|---|---|
| GPIO 17 | Pin 11 (BCM 17) | Reject Solenoid Pulse Trigger (Active High) |
| DC 3.3V | Pin 1 (3V3) | Relay VCC Logic Power |
| GND | Pin 6 (Ground) | Relay Logic Ground |
| Emergency Interlock | Pin 16 (BCM 23) | Hardware Safety Line (Optional) |

---

## 6. Model Lifecycle Workflow
```
[ Development Computer / GPU ]             [ Raspberry Pi Edge Device ]
  1. Train YOLO / MobileNet
  2. Evaluate on Test Dataset
  3. Export to ONNX / INT8
  4. Generate SHA256 Manifest
           |
       SCP / USB Transfer
           |
           v
                                    5. python scripts/deploy_model.py
                                       - Verifies SHA-256 Checksum
                                       - Runs On-Device Smoke Test
                                       - Atomically Promotes to Active
                                       - Archives Previous Version
                                    6. Benchmark On Device:
                                       - python scripts/edge_benchmark.py
                                    7. Instant Rollback if Needed:
                                       - python scripts/rollback_model.py
```

---

## 7. Service Operations
```bash
# Start service
sudo systemctl start can_inspector.service

# View live service logs
journalctl -u can_inspector.service -f

# Check local health endpoint
curl http://localhost:8080/health

# Run camera calibration
python scripts/test_camera.py --adapter picamera2 --frames 20

# Run full hardware benchmark
python scripts/edge_benchmark.py --iterations 100 --target-fps 15.0
```
