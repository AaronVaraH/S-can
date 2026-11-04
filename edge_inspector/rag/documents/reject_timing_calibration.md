# SOP: Reject Actuation Timing Calibration and Encoder Synchronization

## 1. Physical Principle of Pneumatic Reject
A high-speed pneumatic blow-off valve ejects defective cans off the conveyor into a reject chute or accumulation bin.

## 2. Timing Variables
- **Conveyor Velocity ($V_c$)**: Linear belt speed in meters per second (e.g. 1.2 m/s).
- **Physical Separation ($D_{cr}$)**: Distance between the optical axis of the camera inspection station and the center line of the reject blow-off nozzle (nominal: 250 mm).
- **Transit Time ($T_{transit}$)**:
  $$T_{transit} = \frac{D_{cr}}{V_c}$$
  For $D_{cr} = 250\text{ mm}$ and $V_c = 1.2\text{ m/s}$, $T_{transit} = 208.3\text{ ms}$.
- **Inference Latency ($T_{inf}$)**: Time required by Raspberry Pi to acquire, process, and classify the image (e.g. 35 ms).
- **Solenoid Actuation Delay ($T_{solenoid}$)**: Electrical and mechanical pneumatic spool shift delay (typically 8 to 12 ms).
- **Remaining Delay ($T_{wait}$)**:
  $$T_{wait} = T_{transit} - T_{inf} - T_{solenoid}$$
  The reject timer must sleep for $T_{wait}$ before asserting the GPIO reject pulse.

## 3. Pulse Duration Calibration
- Nominal pulse duration: **35 ms to 50 ms**.
- Air pressure: **5.5 to 6.5 bar** clean, dry industrial compressed air.
- If pulse duration is too long (> 70 ms), adjacent cans will be struck (false reject).
- If pulse duration is too short (< 25 ms), heavy full beverage cans will not be completely displaced off the conveyor.

## 4. Industrial Safety Interlock Gate
If total inspection and scheduling latency exceeds $T_{transit} + \text{Tolerance}$ (e.g. > 240 ms), the solenoid MUST be aborted. Striking the wrong can causes line jams and product contamination.
