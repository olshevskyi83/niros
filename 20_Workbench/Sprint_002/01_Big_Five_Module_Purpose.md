# Big Five Module Purpose

## Status

Implementation Design

Sprint 002

---

# Purpose

The Big Five Module is responsible for estimating an individual's stable personality traits using the Five-Factor Model (FFM).

The module transforms questionnaire responses into structured psychological signals that can be interpreted by the NIROS Psychological Engine.

It is not intended to diagnose mental disorders or determine therapeutic decisions independently.

---

# Primary Objective

Generate a reliable personality profile that becomes one component of the overall NIROS psychological representation.

The module provides standardized trait estimates that other modules can combine with additional psychological information.

---

# Inputs

The module accepts:

- questionnaire responses
- response metadata
- response time (optional)
- skipped questions
- confidence indicators
- future conversational evidence

---

# Outputs

The module produces:

- Big Five trait scores
- facet scores (if available)
- confidence estimation
- response consistency metrics
- quality indicators
- structured psychological signals

---

# Five Core Traits

The module estimates:

- Openness to Experience
- Conscientiousness
- Extraversion
- Agreeableness
- Neuroticism

Each trait is represented on a continuous scale rather than as a categorical label.

---

# Role Inside NIROS

The module is an assessment component.

It does not generate therapeutic recommendations.

Instead, it provides personality information to downstream reasoning systems.

```

```text
Questionnaire

↓

Scoring Engine

↓

Trait Scores

↓

Psychological Signals

↓

Reasoning Engine

↓

Personalized Recommendations
```

---

# Responsibilities

The module is responsible for:

- administering personality questions
- validating responses
- calculating trait estimates
- estimating confidence
- detecting inconsistent responding
- producing structured output

---

# Non-Responsibilities

The module is NOT responsible for:

- psychiatric diagnosis
- psychedelic suitability
- therapeutic planning
- risk assessment
- intervention recommendations

Those responsibilities belong to higher-level NIROS modules.

---

# Consumers

The output of this module is used by:

- Reasoning Engine
- Psychological Profile Engine
- Recommendation Engine
- Conversation Assessment Module
- Report Generator

---

# Design Principles

The module should be:

- scientifically grounded
- modular
- deterministic
- explainable
- extensible
- independent of UI
- independent of LLMs

---

# Success Criteria

The module is considered successful when it can reliably convert raw questionnaire responses into a standardized personality representation that can be integrated with every other NIROS psychological module.