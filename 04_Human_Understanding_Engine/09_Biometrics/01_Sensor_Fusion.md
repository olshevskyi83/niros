# Sensor Fusion

Sensor Fusion combines multiple physiological signals with conversation context.

## Inputs

```mermaid
flowchart LR
    HRV[HRV] --> Fusion[Sensor Fusion]
    HR[Heart Rate] --> Fusion
    EDA[EDA] --> Fusion
    Sleep[Sleep] --> Fusion
    Voice[Voice features] --> Fusion
    Breath[Breathing] --> Fusion
    Fusion --> State[Psychophysiological state estimate]
```

## Outputs

- arousal_level
- recovery_status
- stress_response_flag
- signal_quality
- confidence
- suggested_interview_adjustment

## Safety

Never present sensor interpretation as certainty.
