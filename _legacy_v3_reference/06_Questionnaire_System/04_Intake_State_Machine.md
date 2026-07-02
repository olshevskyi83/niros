# Intake State Machine

## Purpose

The intake process should be controlled, repeatable, and auditable.

## States

```text
START
  → CONSENT_AND_SCOPE
  → DECLARED_PROBLEM_CAPTURE
  → NARRATIVE_CLARIFICATION
  → CLINICAL_SCREENING
  → WORLDVIEW_AND_SYMBOLIC_PROFILE
  → VOICE_MUSIC_PREFERENCES
  → SENSOR_CONTEXT_CHECK
  → AI_PROBLEM_INTERPRETATION
  → USER_CONFIRMATION
  → SAFETY_REVIEW
  → PROFILE_LOCK
  → SESSION_PROTOCOL_GENERATION
```

## Stop states

- `CRISIS_SUPPORT_REQUIRED`
- `CONTRAINDICATION_REVIEW_REQUIRED`
- `HUMAN_REVIEW_REQUIRED`
- `INSUFFICIENT_DATA`

## Important rule

The system may generate a soft profile before confirmation, but it must not generate a final session protocol until the profile is confirmed or reviewed.
