# Industrial Edge-AI Troubleshooting & Recovery Playbook

## 1. Safety and Operational Warnings
> [!CAUTION]
> Pneumatic blow-off actuators operate at high velocities and pressures (5.5 to 6.5 bar). Always disengage the physical air supply or engage the software safety interlock before performing mechanical or electrical maintenance near the inspection station.

---

## 2. Common Faults and Solutions

### Symptom A: Camera Disconnects or Freezes
- **Root Cause**: USB power droop, mechanical vibration on USB/CSI connector, or camera firmware freeze.
- **System Behavior**: Watchdog marks health as `DEGRADED` / `CAMERA_DISCONNECTED`. Auto-reconnect attempts backoff every 2 seconds.
- **Recovery Procedure**:
  1. Check camera status: `curl http://localhost:8080/camera/status`
  2. Inspect V4L2 device listing: `v4l2-ctl --list-devices`
  3. For CSI cameras: check ribbon cable seating and test with `rpicam-hello`
  4. If USB camera disconnected: ensure USB camera is connected to a USB 3.0 (blue) port or powered industrial USB hub to prevent 5V bus drops.

### Symptom B: High False Rejects / Quality Gate Rejections (`BLURRY_IMAGE`)
- **Root Cause**: Excessive conveyor speed exceeding lens shutter speed, optical vibration, or focal ring shift.
- **Diagnostics**:
  1. Check average sharpness: `python scripts/test_camera.py --frames 20`
  2. Check image samples in `data/inspections/` for motion blur.
- **Recovery Procedure**:
  1. Reduce exposure time in `config/config.default.yaml`:
     ```yaml
     camera:
       exposure_time_us: 2000  # Decrease to 2ms or 1.5ms
     ```
  2. Tighten manual lens focus and aperture lock screws.
  3. Ensure camera mount is mechanically isolated from the conveyor drive motor frame.

### Symptom C: Specular Glare / Washed-Out Metal Reflections
- **Root Cause**: Direct directional LED spotlight on bare aluminum or tinplate cans.
- **System Behavior**: Quality gate triggers `EXCESSIVE_GLARE (> 12%)` and routes cans to `REVIEW`.
- **Recovery Procedure**:
  1. Replace directional spotlights with a **Diffuse Dome Light** or **Darkfield Ring Light**.
  2. Place a polarizing filter on the camera lens and matching polarizing film over light sources.

### Symptom D: Raspberry Pi Thermal Throttling
- **Root Cause**: Heavy sustained inference on Pi 4/5 without active cooling fan in hot plant environments (> 40°C ambient).
- **Diagnostics**:
  - Run hardware check: `python scripts/check_hardware.py`
  - Read temperature: `vcgencmd measure_temp`
  - Check throttling flags: `vcgencmd get_throttled` (Bit 0x2 = ARM frequency capped; 0x4 = Currently throttled).
- **Recovery Procedure**:
  1. Install the official Raspberry Pi 5 Active Cooler or an aluminum heatsink case.
  2. Reduce thread concurrency in `config/config.default.yaml` (`intra_threads: 3`).
  3. If throughput requirements exceed 25 FPS, deploy the **Raspberry Pi AI HAT+ (Hailo-8 / Hailo-8L)** which offloads neural compute from the CPU at 8x lower power dissipation.

### Symptom E: Conveyor Reject Timing Misalignment (`TIMING_FAULT`)
- **Root Cause**: Conveyor belt speed changed without recalibrating transit delay, or inference latency exceeded the deadline.
- **System Behavior**: Actuator triggers `TIMING_FAULT` safety interlock; blow-off pulse is suppressed to prevent striking an innocent adjacent can.
- **Recovery Procedure**:
  1. Check benchmarked latency: `python scripts/edge_benchmark.py`
  2. Measure conveyor speed with tachometer or encoder.
  3. Update `conveyor_delay_ms` in `config/config.default.yaml`:
     $$T_{transit} = \frac{D_{distance}}{V_{conveyor}}$$
  4. Test pulse alignment with `python -c "from edge_inspector.actuator import create_reject_actuator; a = create_reject_actuator({'adapter':'gpio'}); a.test_pulse()"`

### Symptom F: Disk Space Warning / SD Card Full
- **Root Cause**: Image retention policy keeping too many historical images.
- **System Behavior**: StorageManager automatically prunes oldest PASS and REVIEW images when partition reaches 85%.
- **Recovery Procedure**:
  1. Check disk usage: `df -h`
  2. In `config/config.default.yaml`, verify:
     ```yaml
     storage:
       save_pass_images: false  # Never save PASS images in 24/7 production
       save_fail_images: true
       save_review_images: true
       max_disk_usage_percent: 85.0
     ```
  3. Verify logrotate is executing: `sudo logrotate -f /etc/logrotate.d/can_inspector`
