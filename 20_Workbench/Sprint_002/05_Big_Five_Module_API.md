# Big Five Module API

## Status

Implementation Design

Sprint 002

---

# Purpose

This document defines the API contract for the Big Five Module.

The API is designed as the first implementation of a universal NIROS psychological module interface.

Future modules should follow the same structure whenever possible.

---

# Design Goal

The Big Five Module API must allow NIROS to:

- start an assessment
- present questionnaire items
- receive user responses
- validate responses
- calculate scores
- generate Psychological Signals
- expose results to the Reasoning Engine

The API should not depend on a specific UI.

---

# Core Principle

The module does not return raw questionnaire scores as its final output.

The module returns standardized Psychological Signals.

---

# Module Interface

Every psychological module should expose the following functions:

```python
start_assessment()

submit_response()

validate_responses()

score_assessment()

generate_signals()

get_result()
```

---

# 1. start_assessment()

Starts a new Big Five assessment session.

## Input

```json
{
  "user_id": "user_001",
  "module": "big_five",
  "language": "en",
  "assessment_version": "BFI-2"
}
```

## Output

```json
{
  "assessment_id": "bf_2026_0001",
  "module": "big_five",
  "status": "started",
  "total_items": 60,
  "current_item": 1
}
```

---

# 2. submit_response()

Stores a response to a questionnaire item.

## Input

```json
{
  "assessment_id": "bf_2026_0001",
  "item_id": "BFI2_001",
  "response": 4,
  "response_time_ms": 4200
}
```

## Output

```json
{
  "status": "accepted",
  "item_id": "BFI2_001",
  "next_item": "BFI2_002"
}
```

---

# 3. validate_responses()

Checks whether the assessment can be scored.

## Input

```json
{
  "assessment_id": "bf_2026_0001"
}
```

## Output

```json
{
  "assessment_id": "bf_2026_0001",
  "is_complete": true,
  "missing_items": [],
  "invalid_items": [],
  "quality_warnings": []
}
```

---

# 4. score_assessment()

Calculates Big Five trait and facet scores.

## Input

```json
{
  "assessment_id": "bf_2026_0001"
}
```

## Output

```json
{
  "assessment_id": "bf_2026_0001",
  "module": "big_five",
  "scores": {
    "openness": 76,
    "conscientiousness": 64,
    "extraversion": 48,
    "agreeableness": 71,
    "neuroticism": 39
  },
  "quality": "high",
  "confidence": 0.91
}
```

---

# 5. generate_signals()

Transforms scores into NIROS Psychological Signals.

## Input

```json
{
  "assessment_id": "bf_2026_0001"
}
```

## Output

```json
{
  "assessment_id": "bf_2026_0001",
  "signals": [
    {
      "module": "big_five",
      "signal": "openness",
      "value": 76,
      "confidence": 0.91,
      "source": "BFI-2",
      "evidence": [
        "standardized_questionnaire"
      ],
      "quality": "high"
    }
  ]
}
```

---

# 6. get_result()

Returns the complete assessment result.

## Input

```json
{
  "assessment_id": "bf_2026_0001"
}
```

## Output

```json
{
  "assessment_id": "bf_2026_0001",
  "user_id": "user_001",
  "module": "big_five",
  "status": "completed",
  "assessment_version": "BFI-2",
  "scores": {
    "openness": 76,
    "conscientiousness": 64,
    "extraversion": 48,
    "agreeableness": 71,
    "neuroticism": 39
  },
  "signals": [],
  "quality": "high",
  "confidence": 0.91,
  "created_at": "2026-07-01T12:00:00Z",
  "completed_at": "2026-07-01T12:15:00Z"
}
```

---

# Error Handling

The API should return structured errors.

## Example

```json
{
  "error": true,
  "code": "MISSING_RESPONSES",
  "message": "The assessment contains unanswered items.",
  "details": {
    "missing_items": [
      "BFI2_014",
      "BFI2_039"
    ]
  }
}
```

---

# API Responsibilities

The API is responsible for:

- receiving inputs
- validating responses
- triggering scoring
- returning standardized outputs
- exposing results to the Reasoning Engine

---

# API Non-Responsibilities

The API is not responsible for:

- psychological interpretation
- therapeutic recommendations
- clinical diagnosis
- psychedelic suitability decisions
- conversation-based inference

These responsibilities belong to higher-level NIROS systems.

---

# Integration Contract

The Reasoning Engine should only depend on the module output format, not on internal scoring implementation.

Therefore, every module must eventually expose:

```json
{
  "module": "module_name",
  "signals": []
}
```

This allows NIROS to add new modules without changing the Reasoning Engine interface.

---

# Summary

The Big Five Module API defines the first reusable NIROS psychological module interface.

It receives questionnaire responses, calculates standardized scores and returns Psychological Signals for the Reasoning Engine.

The same interface pattern should be reused by all future NIROS assessment modules.