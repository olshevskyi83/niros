# Big Five Questionnaire Design

## Status

Implementation Design

Sprint 002

---

# Objective

The questionnaire is the first stage of the NIROS personality assessment pipeline.

Its purpose is to estimate the user's Big Five personality traits using a standardized and scientifically validated instrument.

The questionnaire provides the baseline personality profile.

This profile is later refined by the NIROS Conversation Assessment Module and interpreted by the Reasoning Engine.

---

# Design Principles

- Use an established validated questionnaire.
- Preserve standard scoring.
- Do not modify the psychometric properties of the original assessment.
- Allow AI to extend the assessment only after the standardized questionnaire is completed.
- Keep the assessment modular.

# Assessment Strategy

NIROS uses a two-stage personality assessment.

Stage 1

Standardized questionnaire (BFI-2)

↓

Initial personality profile

↓

Stage 2

AI-driven conversational assessment

↓

Confidence estimation

↓

Discrepancy detection

↓

Adaptive follow-up questions

↓

Updated psychological representation

The standardized questionnaire remains unchanged.

AI never overwrites the questionnaire score.

AI provides an independent estimate and additional evidence.

## Selected Assessment

Primary assessment:

BFI-2

Reason:

- strong scientific validation
- broad international use
- 60 items
- 15 facets
- suitable balance between detail and completion time

