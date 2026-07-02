---
type: psychedelic-module
version: v2.0
status: active-mvp
tags: [psilocybin, psychedelic-module, niros]
---

# Psilocybin Module

## Purpose

The Psilocybin Module is the first active psychedelic method module for NIROS MVP.

## Scope

This module supports evidence organization, safety screening, profile-based personalization, session-support structure, and outcome tracking for psilocybin-related research contexts.

## Not included

- dose recommendations;
- mushroom cultivation;
- extraction;
- preparation instructions;
- medical prescriptions;
- claims of cure.

## Inputs

- ParticipantProfile
- SafetyReport
- ClinicalModule
- EvidenceSummary

## Outputs

- method-specific risk notes;
- session context notes;
- preparation themes;
- integration themes;
- scenario constraints.

## Key research areas

- depression;
- anxiety and existential distress;
- addiction;
- chronic pain/fibromyalgia research questions;
- music and set/setting;
- adverse events and screening;
- integration and long-term outcomes.

## Cursor implementation notes

Create machine-readable module file:

```text
modules/psychedelics/psilocybin.json
```

Fields:

```json
{
  "module_id": "psilocybin",
  "status": "active_mvp",
  "allowed_outputs": [],
  "prohibited_outputs": [],
  "safety_flags": [],
  "evidence_tags": [],
  "scenario_constraints": []
}
```
