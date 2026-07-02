---
type: boundary
version: v2.0
status: active
tags: [niros, safety, boundaries]
---

# Project Boundaries

This document defines what NIROS may and may not do.

## Allowed

NIROS may:

- store and organize scientific papers;
- summarize open scientific knowledge;
- build participant profiles from questionnaires;
- flag safety concerns;
- generate non-dosing session support scripts;
- generate facilitator notes;
- generate voice and music guidance;
- log session events;
- track follow-up outcomes;
- compare outcomes across anonymized profiles;
- support research planning.

## Not allowed

NIROS must not:

- diagnose disease;
- claim to treat or cure disease;
- prescribe substances;
- recommend psychedelic dose;
- provide extraction, brewing, preparation, or synthesis instructions;
- tell a person to stop medication;
- replace emergency care;
- encourage unsupervised high-risk use;
- generate claims that are not marked as evidence-based or hypothetical.

## Ayahuasca / DMT special boundary

The ayahuasca / DMT module is allowed only as a research, safety, cultural-context, risk-screening, and session-support-analysis module.

It must not contain:

- recipes;
- plant ratios;
- extraction steps;
- brewing steps;
- dosage guidance;
- MAOI combination instructions.

## Cursor implementation note

Cursor must treat these boundaries as hard requirements. Any code path that creates session materials must check the Safety Engine first and must not output substance preparation or dosage content.
