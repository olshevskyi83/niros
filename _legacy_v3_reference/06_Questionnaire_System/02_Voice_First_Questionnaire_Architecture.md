# Voice-First Questionnaire Architecture

## Purpose

The questionnaire should feel like a natural conversation, not a bureaucratic form.

The user answers by voice. NIROS converts speech into structured data while preserving the original transcript.

## Why voice matters

Voice gives two categories of information:

1. **semantic content** — what the person says,
2. **paralinguistic context** — rhythm, pauses, hesitation, emotional tone, intensity, fatigue, breath pattern.

NIROS must treat voice signals carefully. They are context, not proof.

## Intake stages

### Stage 1 — Opening statement

The user answers:

> What brought you here? What problem do you want help with?

Output:

- declared problem,
- emotional tone,
- main words,
- urgency,
- risk hints.

### Stage 2 — Clarifying narrative

The AI asks:

- When did this start?
- What makes it worse?
- What makes it better?
- What have you already tried?
- What are you afraid might happen?
- What would improvement look like?

### Stage 3 — Structured domains

The conversation covers:

- identity and life context,
- clinical symptoms,
- trauma sensitivity,
- body relationship,
- sleep/fatigue,
- emotional regulation,
- social support,
- worldview and beliefs,
- language and symbolic preferences,
- voice and music preferences,
- contraindications.

### Stage 4 — Sensor sync

The system checks whether wearable/sensor data exists.

Possible sensor sources:

- Apple Watch,
- Garmin,
- Oura,
- phone microphone,
- phone accelerometer,
- manual HRV measurement,
- sleep data,
- respiration estimate.

### Stage 5 — AI summary back to user

The AI returns a short interpretation and asks for correction.

## Data rule

Every voice answer should generate:

```json
{
  "question_id": "string",
  "transcript": "raw user answer",
  "structured_answer": {},
  "confidence": "low|medium|high",
  "emotional_markers": [],
  "safety_flags": [],
  "needs_human_review": false
}
```

## Product rule

The first MVP can start with voice transcription + structured questionnaire.

Advanced voice biomarkers should be added later and validated separately.
