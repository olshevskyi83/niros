# Sensor-Assisted Intake and Monitoring

## Purpose

Sensors help NIROS understand the body state before and during a session.

They do not replace medical assessment.

## Intake sensor use

Before a session, sensors may help estimate:

- baseline heart rate,
- HRV range,
- sleep debt,
- fatigue,
- stress load,
- respiration rhythm,
- restlessness,
- recovery state.

## Session sensor use

During a session, sensors may help detect:

- excessive physiological activation,
- panic-like escalation,
- freezing/shutdown patterns,
- unusually high arousal,
- possible need to slow down the audio/script.

## Possible devices

- Apple Watch,
- Garmin,
- Oura,
- Polar H10,
- phone camera PPG,
- phone accelerometer,
- microphone-derived respiration estimate.

## Design principle

Sensor data should influence intensity and pacing, not create medical claims.

Example:

- lower audio intensity,
- slower voice pacing,
- grounding segment,
- pause sequence,
- human facilitator alert.

## Output object

```json
{
  "hr_baseline": null,
  "hrv_baseline": null,
  "sleep_quality": null,
  "respiration_estimate": null,
  "movement_restlessness": null,
  "stress_context": "unknown",
  "sensor_confidence": "low",
  "recommended_session_intensity": "conservative"
}
```
