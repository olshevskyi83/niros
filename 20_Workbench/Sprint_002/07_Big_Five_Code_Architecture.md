# Big Five Code Architecture

## Status

Implementation Design

Sprint 002

---

# Purpose

This document defines the internal software architecture of the NIROS Big Five Module.

The objective is to provide a clean, modular and maintainable implementation that can serve as the template for all future psychological assessment modules.

The architecture separates questionnaire management, scoring, signal generation and reasoning integration into independent components.

---

# Design Principles

The implementation should be:

- modular
- testable
- deterministic
- explainable
- reusable
- independent of UI
- independent of database
- independent of LLM providers

Each component should have a single responsibility.

---

# Directory Structure

```
big_five/

│

├── questions.py

├── questionnaire.py

├── validation.py

├── scoring.py

├── normalization.py

├── confidence.py

├── signals.py

├── models.py

├── api.py

├── exceptions.py

├── config.py

└── tests/
```

---

# Component Responsibilities

## questions.py

Stores questionnaire metadata.

Responsibilities:

- BFI-2 items
- response scale
- reverse items
- facet mapping
- trait mapping

No scoring logic.

---

## questionnaire.py

Controls assessment flow.

Responsibilities:

- start assessment
- next question
- previous question
- save responses
- assessment progress

No scoring.

---

## validation.py

Validates questionnaire integrity.

Responsibilities:

- missing responses
- invalid values
- duplicated answers
- response completeness
- response consistency

---

## scoring.py

Implements official BFI-2 scoring.

Responsibilities:

- reverse scoring
- trait calculation
- facet calculation
- raw scores

No interpretation.

---

## normalization.py

Converts raw scores into standardized NIROS values.

Responsibilities:

- normalization
- scaling
- standard score generation

---

## confidence.py

Calculates confidence estimates.

Possible inputs:

- response consistency
- completion rate
- quality indicators
- future conversation agreement

Produces:

Confidence Score

---

## signals.py

Transforms scores into NIROS Psychological Signals.

Responsibilities:

- signal generation
- metadata creation
- evidence tracking

Produces:

Psychological Signal objects.

---

## models.py

Defines internal data models.

Examples:

Assessment

Response

Trait

Facet

PsychologicalSignal

AssessmentResult

---

## api.py

Public interface.

Responsibilities:

- start assessment
- submit response
- score assessment
- generate signals
- return result

This is the only entry point used by external NIROS components.

---

## exceptions.py

Contains all module-specific exceptions.

Examples:

IncompleteAssessment

InvalidResponse

ScoringError

ConfigurationError

---

## config.py

Module configuration.

Examples:

Questionnaire version

Normalization settings

Confidence thresholds

Feature flags

---

## tests/

Contains automated tests.

Tests should include:

- questionnaire validation
- reverse scoring
- trait scoring
- facet scoring
- normalization
- signal generation
- API behaviour
- regression tests

---

# Internal Workflow

```
questions.py

↓

questionnaire.py

↓

validation.py

↓

scoring.py

↓

normalization.py

↓

confidence.py

↓

signals.py

↓

api.py

↓

Reasoning Engine
```

Every component performs one task only.

---

# Dependency Rules

Allowed dependencies:

questionnaire

↓

validation

↓

scoring

↓

normalization

↓

confidence

↓

signals

↓

api

Reverse dependencies are not allowed.

No circular imports.

---

# Future Extensibility

The architecture should support:

- multilingual questionnaires
- adaptive questioning
- repeated assessments
- clinician review
- AI conversation evidence
- longitudinal personality tracking

No major architectural changes should be required.

---

# Relationship with NIROS Core

The Big Five Module is completely independent.

It communicates with the rest of NIROS only through:

- standardized API
- Psychological Signals

The module has no knowledge of:

- psychedelic recommendations
- diagnosis
- treatment planning
- other assessment modules

These responsibilities belong to the NIROS Psychological Engine.

---

# Template for Future Modules

Future modules should follow the same architecture.

Examples:

attachment/

emotion_regulation/

trauma/

suggestibility/

values/

motivation/

Each module should expose the same API and produce standardized Psychological Signals.

This guarantees consistency across the entire NIROS ecosystem.

---

# Summary

The Big Five Code Architecture defines the first production-ready psychological assessment module for NIROS.

The architecture separates questionnaire management, validation, scoring, confidence estimation, signal generation and API access into independent components.

This implementation serves as the reference architecture for every future NIROS psychological module.