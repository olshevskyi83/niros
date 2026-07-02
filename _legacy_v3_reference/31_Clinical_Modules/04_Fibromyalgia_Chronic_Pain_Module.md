---
type: clinical-module
version: v2.0
status: active-mvp
tags: [clinical-module, fibromyalgia_chronic_pain, niros]
---

# Fibromyalgia / Chronic Pain Module

## Purpose

Define the NIROS research and personalization structure for `fibromyalgia_chronic_pain` in psychedelic-session-support contexts.

## Scope

This module organizes condition-specific evidence, profile signals, safety concerns, outcome measures, and scenario constraints.

It does not diagnose, treat, or claim cure.

## Psychological targets

pain fear, fatigue, body vigilance, sleep disruption, helplessness

## Scenario style

body-respectful, validating, non-cure-claim, safety-oriented

## Inputs

- ParticipantProfile
- SafetyReport
- PsychedelicModule
- EvidenceSummary
- Clinical-specific questionnaire block

## Outputs

- clinical module profile notes;
- scenario constraints;
- integration focus;
- outcome tracking suggestions;
- evidence gaps;
- safety notes.

## Safety concerns

Safety concerns must be defined in module JSON and passed to the Safety Engine.

## Outcome measures

MVP can use simplified self-report scales before validated scales are integrated.

## Research questions

- Which participant profile patterns appear linked to better integration outcomes?
- Which voice/music/session timing features correlate with reported benefit or distress?
- Which safety flags predict difficult sessions or poor follow-up outcomes?

## Cursor implementation notes

Create module file:

```text
modules/clinical/fibromyalgia_chronic_pain.json
```

Use the standard schema from [[02_Project_Architecture/03_Module_Contract_Standard]].
