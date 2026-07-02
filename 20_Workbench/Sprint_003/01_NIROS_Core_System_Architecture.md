# NIROS Core System Architecture

## Status

Architecture Design

Sprint 003

---

# Purpose

This document defines the high-level architecture of NIROS Core.

NIROS Core is the central system that connects psychological assessment modules, AI conversation, reasoning, profile generation and recommendation logic into one coherent Psychological Engine.

The goal is to avoid building separate questionnaires and instead create a modular system where every component contributes structured psychological evidence.

---

# Core Idea

NIROS is not a test system.

NIROS is a psychological reasoning platform.

Each module produces Psychological Signals.

The Core Engine integrates those signals into a unified psychological profile.

The system then uses this profile to support personalized preparation, reflection and integration around psychedelic experiences.

---

# High-Level Architecture

```text
User Interface

↓

Assessment Modules

↓

Psychological Signals

↓

Module Registry

↓

Psychological Profile Engine

↓

Reasoning Engine

↓

Recommendation Interface

↓

Personalized Output
```

---

# Main Components

## 1. User Interface

The UI is responsible for interaction only.

It may present:

- questionnaires
- conversational prompts
- progress indicators
- reports
- preparation guidance

The UI does not perform scoring or reasoning.

---

## 2. Assessment Modules

Assessment modules measure specific psychological domains.

Examples:

- Big Five
- Attachment
- Emotion Regulation
- Absorption
- Suggestibility
- Trauma
- Values
- Cognitive Style
- Motivation
- Psychedelic History
- Mental Health Screening
- Conversation-based AI Assessment

Each module is independent.

Each module exposes a standard API.

Each module produces Psychological Signals.

---

## 3. Psychological Signals

Psychological Signals are the standard output format of all modules.

A signal contains:

- module
- signal name
- value
- confidence
- source
- evidence
- quality
- metadata

Signals allow NIROS to combine data from different modules without hardcoding module-specific logic.

---

## 4. Module Registry

The Module Registry tracks available psychological modules.

It knows:

- which modules exist
- which modules are active
- what signals each module can produce
- what dependencies each module has
- what version each module uses

The registry allows NIROS to scale without rewriting the Core Engine.

---

## 5. Psychological Profile Engine

The Psychological Profile Engine stores and updates the user's unified psychological profile.

It receives Psychological Signals from modules and organizes them into a coherent representation.

It does not make final recommendations.

Its job is profile construction.

---

## 6. Reasoning Engine

The Reasoning Engine interprets the profile.

It identifies:

- patterns
- conflicts
- risks
- strengths
- preparation needs
- uncertainty
- missing information

It works across multiple modules rather than relying on a single test.

---

## 7. Conversation Assessment Engine

The Conversation Assessment Engine extracts psychological evidence from dialogue.

It can:

- ask follow-up questions
- detect inconsistencies
- refine confidence
- produce conversational Psychological Signals
- request additional module assessments

It does not overwrite standardized questionnaire results.

---

## 8. Recommendation Interface

The Recommendation Interface receives interpreted psychological information from the Reasoning Engine.

It may generate:

- preparation focus areas
- reflection prompts
- session support considerations
- integration themes
- communication recommendations

It does not receive raw questionnaire responses.

---

# Core Data Flow

```text
User response

↓

Module API

↓

Validation

↓

Scoring

↓

Psychological Signal

↓

Module Registry

↓

Profile Engine

↓

Reasoning Engine

↓

Recommendation Interface
```

---

# Separation of Responsibilities

## Modules

Measure specific psychological domains.

## Profile Engine

Stores and integrates signals.

## Reasoning Engine

Interprets patterns across domains.

## Recommendation Interface

Transforms reasoning output into user-facing guidance.

## UI

Displays and collects information.

---

# What NIROS Core Must Not Do

NIROS Core must not:

- hardcode questionnaire logic
- directly modify module scores
- confuse assessment with recommendation
- allow one module to decide therapeutic suitability
- depend on a specific LLM provider
- depend on a specific user interface

---

# Design Principles

NIROS Core should be:

- modular
- explainable
- extensible
- source-aware
- confidence-aware
- evidence-based
- testable
- provider-independent
- UI-independent

---

# Example System Behaviour

Example:

Big Five Module produces:

- High Openness
- Medium Neuroticism
- Low Conscientiousness

Attachment Module produces:

- High Attachment Anxiety

Emotion Regulation Module produces:

- High Emotional Suppression

Conversation Engine detects:

- difficulty describing emotions

Reasoning Engine integrates:

- emotional intensity risk
- need for structured preparation
- importance of grounding practices
- need for careful integration support

Recommendation Interface generates:

- preparation focus
- reflection prompts
- support considerations

No single module makes the final interpretation.

---

# Architecture Rule

Every new NIROS module must follow this rule:

```text
Module Input

↓

Module Logic

↓

Psychological Signals

↓

Core Engine
```

Modules should never directly control recommendations.

---

# Summary

NIROS Core is the central architecture that transforms independent psychological modules into a unified Psychological Engine.

Its foundation is the Psychological Signal model.

Every module contributes structured evidence.

The Profile Engine organizes this evidence.

The Reasoning Engine interprets it.

The Recommendation Interface converts it into practical personalized guidance.