# Universal Psychological Signal Model

## Status

Architecture Design

Sprint 003

---

# Purpose

This document defines the Universal Psychological Signal Model (UPSM), the foundational data representation used throughout NIROS.

Every assessment module, regardless of psychological domain, communicates with the NIROS Core through Psychological Signals.

This model provides a common language that allows independent modules to interact without knowing each other's internal implementation.

---

# Philosophy

Traditional psychological software stores questionnaire scores.

NIROS stores evidence.

Every Psychological Signal represents one piece of evidence describing an individual's psychological functioning.

The NIROS Core integrates these pieces of evidence into a unified psychological representation.

---

# Definition

A Psychological Signal is the smallest standardized unit of psychological information within NIROS.

It represents an estimate of one measurable psychological construct together with its supporting evidence and confidence.

Examples include:

- Openness
- Emotional Suppression
- Attachment Anxiety
- Psychological Flexibility
- Curiosity
- Cognitive Rigidity
- Suggestibility
- Trauma Severity

---

# Core Principles

Every Psychological Signal must be:

- standardized
- interpretable
- traceable
- confidence-aware
- evidence-based
- independent from implementation details

Signals must never contain therapeutic recommendations.

Signals describe observations, not conclusions.

---

# Universal Signal Structure

Every Psychological Signal contains:

- Module
- Signal Name
- Value
- Confidence
- Evidence
- Source
- Quality
- Timestamp
- Metadata

---

# Module

The module that generated the signal.

Examples:

- Big Five
- Attachment
- Trauma
- Values
- Conversation Assessment

---

# Signal Name

A unique identifier describing the measured psychological construct.

Examples:

- openness
- agreeableness
- attachment_anxiety
- emotional_suppression
- cognitive_flexibility

Signal names should remain stable across NIROS versions.

---

# Value

Represents the estimated strength of the construct.

Default internal representation:

0–100

Interpretation:

0

Extremely low

50

Average

100

Extremely high

Individual modules may use different internal calculations, but the exported signal must use the standardized scale.

---

# Confidence

Confidence estimates how reliable the signal is.

Range:

0.0 – 1.0

Confidence depends on:

- assessment quality
- amount of evidence
- response consistency
- cross-module agreement
- conversation verification

Confidence is never equal to the signal value.

---

# Evidence

Evidence records how NIROS produced the signal.

Possible evidence includes:

- standardized questionnaire
- conversational interview
- adaptive questions
- clinician review
- repeated assessment
- longitudinal observation

A signal may contain multiple evidence sources.

---

# Source

Identifies the assessment instrument.

Examples:

- BFI-2
- ERQ
- IPIP
- Conversation AI
- Clinician Review

This preserves transparency.

---

# Quality

Overall integrity of the signal.

Possible values:

- High
- Medium
- Low

Quality summarizes the reliability of the assessment process.

---

# Timestamp

Records when the signal was generated.

Required for:

- longitudinal analysis
- reassessment
- profile evolution

---

# Metadata

Optional information specific to the generating module.

Examples:

- questionnaire version
- language
- assessment duration
- missing items
- scoring version
- AI model version

---

# Example Signal

```json
{
  "module": "big_five",
  "signal": "openness",
  "value": 76,
  "confidence": 0.91,
  "source": "BFI-2",
  "evidence": [
    "standardized_questionnaire",
    "conversation_assessment"
  ],
  "quality": "high",
  "timestamp": "2026-07-01T12:45:00Z",
  "metadata": {
    "assessment_version": "BFI-2",
    "language": "English"
  }
}
```

---

# Multiple Signals

Different modules may produce evidence for the same construct.

Example:

Big Five

↓

Openness = 74

Conversation Assessment

↓

Openness = 79

Values Module

↓

Curiosity = High

These signals remain independent.

They are never merged inside individual modules.

Integration occurs only inside the Reasoning Engine.

---

# Signal Lifecycle

```text
Assessment

↓

Raw Responses

↓

Scoring

↓

Psychological Signal

↓

Profile Engine

↓

Reasoning Engine

↓

Integrated Psychological Profile
```

Signals remain immutable after creation.

New evidence generates new signals rather than modifying existing ones.

---

# Versioning

Each signal stores:

- module version
- assessment version
- scoring version
- generation timestamp

This guarantees reproducibility.

---

# Future Compatibility

The Universal Psychological Signal Model is designed to support future data sources including:

- wearable devices
- physiological measurements
- behavioural observations
- voice analysis
- facial expression analysis
- digital biomarkers
- future AI models

No changes to the Core Engine should be required.

---

# Design Rule

Every new NIROS module must satisfy one requirement:

Input

↓

Internal Module Logic

↓

Universal Psychological Signal

↓

NIROS Core

Modules never communicate directly with one another.

Psychological Signals are the only shared language inside NIROS.

---

# Summary

The Universal Psychological Signal Model is the foundation of the NIROS architecture.

It replaces isolated questionnaire scores with standardized evidence objects.

This design allows NIROS to integrate information from any psychological assessment module while maintaining transparency, modularity and explainability.