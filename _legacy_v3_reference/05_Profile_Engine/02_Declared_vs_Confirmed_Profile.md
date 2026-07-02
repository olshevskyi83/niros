# Declared vs Confirmed Profile

## Problem

People often arrive with one stated explanation:

- depression,
- anxiety,
- trauma,
- chronic pain,
- addiction,
- existential crisis,
- relationship loss,
- burnout.

But the real therapeutic target may be different or more layered.

Example:

A user may say: "I came because of depression."

The deeper profile may suggest:

- unresolved grief,
- emotional suppression,
- chronic stress physiology,
- low social support,
- shame loop,
- sleep collapse,
- trauma sensitivity,
- contraindication risk.

## Model

NIROS separates three layers.

### 1. Declared Problem

What the user says first.

### 2. Inferred Pattern

What the AI infers from:

- voice answers,
- structured questionnaire,
- clinical screening,
- worldview profile,
- physiological context,
- safety markers.

### 3. Confirmed Therapeutic Target

The target selected after user confirmation.

## Rule

The system should say something like:

> You came with depression as the main problem. From your answers, it looks like the core pattern may be chronic emotional exhaustion, unresolved grief, and loss of meaning. Does this feel accurate, partially accurate, or wrong?

The user must be able to correct the AI.

## Output

```json
{
  "declared_problem": "depression",
  "inferred_pattern": ["grief", "emotional exhaustion", "loss of meaning"],
  "confidence": "medium",
  "user_confirmation": "partially accurate",
  "confirmed_target": "grief-linked depressive exhaustion"
}
```
