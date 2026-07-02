# v3 Architecture Extension

## Purpose

This document defines the v3 expansion of NIROS.

v3 adds four major capabilities:

1. voice-first intake,
2. sensor-assisted context,
3. AI confirmation of the user's real therapeutic target,
4. operational workflows for idea capture and development.

## v3 intake pipeline

```text
User speech
  ↓
Speech-to-text
  ↓
Declared Problem Hypothesis
  ↓
Voice-first questionnaire
  ↓
Clinical and safety screening
  ↓
Sensor context
  ↓
Profile Engine
  ↓
AI Problem Confirmation
  ↓
Confirmed Therapeutic Target
  ↓
Protocol / Music / Session Engine
```

## Critical design rule

The system must never jump directly from user complaint to session generation.

There must be an interpretation layer between:

- what the user says,
- what the system infers,
- what is safe to do,
- what the user confirms.

## Sensor rule

Sensor data can support personalization and safety monitoring, but it must not be treated as a standalone diagnostic authority.

Examples of useful signals:

- HRV baseline,
- heart rate reactivity,
- respiration rhythm,
- sleep/fatigue state,
- motion/restlessness,
- voice stress markers.

## Output objects

The v3 architecture should produce these structured objects:

- `declared_problem`
- `intake_transcript`
- `profile_summary`
- `sensor_context`
- `safety_flags`
- `confirmed_target`
- `session_recommendation`
- `explanation_for_user`
- `traceability_record`
