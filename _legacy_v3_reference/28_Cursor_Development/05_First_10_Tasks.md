---
type: task-plan
version: v2.0
status: active
tags: [cursor, mvp, tasks]
---

# First 10 Cursor Tasks

## Task 1 — Project skeleton

Create folders, README, requirements, `.env.example`, `.gitignore`.

## Task 2 — Config

Implement `src/config.py` with local paths and app mode.

## Task 3 — Schemas

Create base Pydantic models for QuestionnaireResponse, ParticipantProfile, SafetyReport, EvidenceSummary, ScenarioScript.

## Task 4 — Module JSON

Create `modules/psychedelics/psilocybin.json` and first clinical module JSON files.

## Task 5 — Questionnaire loader

Load questionnaire JSON and validate answers.

## Task 6 — Profile Engine

Convert questionnaire response into ParticipantProfile.

## Task 7 — Safety Engine

Generate SafetyReport and enforce risk levels.

## Task 8 — Streamlit Intake UI

Create basic intake page and save response locally.

## Task 9 — Scenario Generator stub

Generate a safe mock Markdown report from profile + safety + module data. No LLM yet.

## Task 10 — Demo profile test

Add demo profiles and test full flow locally.
