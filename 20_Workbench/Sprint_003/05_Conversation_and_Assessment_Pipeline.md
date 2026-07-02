# Conversation and Assessment Pipeline

## Status

Architecture Design

Sprint 003

---

# Purpose

This document defines the complete user journey through the NIROS assessment process.

Rather than presenting a collection of disconnected psychological tests, NIROS provides a single adaptive interview that combines standardized assessments with AI-guided conversation.

The objective is to create the most accurate psychological representation while keeping the user experience natural and engaging.

---

# Core Principle

The user should never feel that they are completing twelve different psychological questionnaires.

Instead, they experience one intelligent conversation.

Internally, NIROS coordinates multiple psychological modules that contribute evidence to the same Psychological Profile.

---

# Assessment Pipeline

```
User

↓

Introduction

↓

Initial Screening

↓

Standardized Assessments

↓

Psychological Signals

↓

Conversation Assessment

↓

Adaptive Follow-up

↓

Psychological Profile

↓

Reasoning Engine

↓

Personalized Recommendations

↓

Session Preparation

↓

Integration Support

↓

Longitudinal Profile Update
```

---

# Stage 1 — Introduction

NIROS explains:

- the purpose of the assessment
- expected duration
- privacy principles
- how the information will be used

The goal is to establish trust and informed participation.

---

# Stage 2 — Initial Screening

NIROS performs a brief intake.

Examples include:

- age
- language
- previous psychedelic experience
- immediate safety screening

The screening determines which modules should be activated.

---

# Stage 3 — Standardized Assessments

NIROS administers validated psychological questionnaires.

Examples:

- Big Five
- Attachment
- Emotion Regulation
- Trauma
- Values

Each module independently generates Psychological Signals.

Standardized scoring is never modified.

---

# Stage 4 — Conversation Assessment

After the questionnaires, NIROS begins an adaptive conversation.

The Conversation Engine may:

- clarify ambiguous responses
- explore psychological themes
- identify inconsistencies
- estimate confidence
- collect additional evidence

Conversation does not replace standardized assessment.

It complements it.

---

# Stage 5 — Adaptive Follow-up

If confidence remains low or evidence is contradictory, NIROS requests additional information.

Possible strategies include:

- targeted follow-up questions
- repeated questionnaire items
- conversational clarification
- future reassessment

Adaptive questioning is driven by uncertainty rather than by a fixed script.

---

# Stage 6 — Psychological Profile

The Profile Engine integrates all available Psychological Signals into a unified psychological representation.

The profile remains dynamic and accumulates evidence over time.

No assessment result is discarded.

---

# Stage 7 — Reasoning

The Reasoning Engine evaluates:

- agreement between modules
- conflicting evidence
- confidence
- missing information
- psychological patterns

The engine produces explainable internal reasoning.

---

# Stage 8 — Personalized Recommendations

Recommendations are generated only after reasoning is complete.

Examples include:

- preparation priorities
- communication style
- emotional support considerations
- reflective exercises
- integration themes

Recommendations are based on multiple evidence sources.

No single assessment determines the final output.

---

# Stage 9 — Longitudinal Learning

Future assessments are compared with previous Psychological Signals.

NIROS tracks:

- profile stability
- confidence changes
- new evidence
- psychological development

The profile evolves continuously rather than being recreated from scratch.

---

# User Experience Principles

The assessment should feel:

- conversational
- respectful
- adaptive
- transparent
- scientifically grounded
- personalized

The user should never feel overwhelmed by psychological terminology or repetitive questionnaires.

---

# System Principles

Internally NIROS always follows the same sequence:

```
Assessment

↓

Psychological Signals

↓

Profile Engine

↓

Reasoning Engine

↓

Recommendations
```

Every module follows this architecture.

---

# Future Extensions

The pipeline is designed to support future capabilities such as:

- clinician-assisted interviews
- voice interaction
- multimodal behavioural analysis
- wearable data
- longitudinal monitoring
- additional psychological modules

No major architectural redesign should be required.

---

# Summary

NIROS delivers a unified psychological assessment experience rather than a collection of independent tests.

Validated questionnaires provide standardized evidence.

AI-guided conversation expands and verifies that evidence.

The Profile Engine organizes it.

The Reasoning Engine interprets it.

The result is a continuously evolving psychological profile capable of supporting personalized preparation, reflection and integration.