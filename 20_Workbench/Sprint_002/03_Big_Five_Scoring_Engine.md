# Big Five Scoring Engine

## Status

Implementation Design

Sprint 002

---

# Purpose

This document defines how the NIROS Big Five Module transforms raw questionnaire responses into standardized psychological signals.

The scoring engine follows the official BFI-2 methodology while extending it with additional quality assessment and confidence estimation.

The goal is to preserve the scientific validity of the questionnaire while providing richer information for the NIROS Reasoning Engine.

---

# Design Principles

The scoring engine must be:

- deterministic
- reproducible
- transparent
- scientifically grounded
- compatible with BFI-2
- explainable
- extensible

The standard BFI-2 score is never modified by AI.

AI-generated information is stored separately.

---

# Assessment Pipeline

The scoring process consists of several stages.

```
Questionnaire

↓

Response Validation

↓

Reverse Scoring

↓

Trait Calculation

↓

Facet Calculation

↓

Normalization

↓

Quality Assessment

↓

Confidence Estimation

↓

Psychological Signals

↓

Reasoning Engine
```

---

# Stage 1 — Response Validation

Before scoring begins, NIROS validates the questionnaire.

Validation checks include:

- unanswered questions
- duplicate responses
- invalid values
- interrupted assessments
- questionnaire completeness

If validation fails, the assessment is marked as incomplete.

---

# Stage 2 — Reverse Scoring

BFI-2 contains positively and negatively worded items.

Reverse items are automatically inverted before trait calculation.

Example:

```
Original Response

5

↓

Reverse Item

↓

1
```

The reverse-scoring procedure follows the official BFI-2 specification.

---

# Stage 3 — Trait Calculation

Responses are grouped according to the official BFI-2 scoring key.

The scoring engine calculates five primary personality traits.

- Openness
- Conscientiousness
- Extraversion
- Agreeableness
- Neuroticism

Trait values are initially calculated using the official scoring procedure.

---

# Stage 4 — Facet Calculation

Whenever possible, NIROS also calculates the fifteen BFI-2 facets.

These facet scores provide a more detailed personality representation.

Facet scores remain linked to their parent trait.

---

# Stage 5 — Normalization

Raw scores are transformed into standardized values.

Internal representation:

0–100

Where

0 = extremely low

50 = average

100 = extremely high

Normalization is performed independently for each trait.

---

# Stage 6 — Quality Assessment

NIROS evaluates the overall quality of the questionnaire.

Quality indicators include:

- completion rate
- response consistency
- excessive neutral responding
- response variability
- unusually fast completion
- contradictory answer patterns

Overall quality is classified as:

- High
- Medium
- Low

---

# Stage 7 — Confidence Estimation

Confidence is calculated independently from personality scores.

Confidence depends on:

- questionnaire completeness
- consistency
- missing answers
- internal reliability
- agreement with future Conversation Assessment

Confidence ranges from:

0.0

to

1.0

Examples:

0.95

Very reliable assessment

0.60

Moderate certainty

0.30

Low confidence

---

# Stage 8 — Psychological Signal Generation

Each calculated trait becomes a standardized Psychological Signal.

Example:

```json
{
  "module": "big_five",
  "signal": "openness",
  "value": 74,
  "confidence": 0.91,
  "source": "BFI-2",
  "quality": "high"
}
```

The scoring engine produces five primary signals.

Future versions may additionally generate fifteen facet-level signals.

---

# AI Integration

The scoring engine itself never changes questionnaire scores.

Instead, NIROS stores AI-generated evidence separately.

Example:

Questionnaire

↓

Openness = 74

Conversation Assessment

↓

Estimated Openness = 79

Reasoning Engine

↓

Integrates both sources.

Original questionnaire scores remain unchanged.

---

# Error Handling

Possible assessment errors include:

- incomplete questionnaire
- invalid responses
- corrupted data
- unsupported questionnaire version

Errors are reported separately from personality scores.

---

# Versioning

Every assessment records:

- questionnaire version
- scoring algorithm version
- normalization version

This ensures reproducibility of results across future NIROS releases.

---

# Summary

The Big Five Scoring Engine converts standardized BFI-2 responses into structured Psychological Signals.

The engine preserves the original scientific scoring methodology while enriching the assessment with confidence estimates, quality metrics and standardized outputs for the NIROS Psychological Engine.

The scoring engine never performs psychological interpretation.

Interpretation is the responsibility of the NIROS Reasoning Engine.