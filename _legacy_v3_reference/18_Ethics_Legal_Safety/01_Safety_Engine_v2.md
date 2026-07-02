---
type: module-spec
version: v2.0
status: active
tags: [safety-engine, ethics, niros]
---

# Safety Engine v2

## Purpose

The Safety Engine identifies risk flags before any session-support material is generated.

## Scope

It does not diagnose, prescribe, or clear a person for psychedelic use. It produces a structured risk report and recommends escalation when needed.

## Inputs

- ParticipantProfile
- medical safety questionnaire block
- medication list
- psychiatric history fields
- method module safety rules
- clinical module risk rules

## Outputs

- SafetyReport
- risk level
- red flags
- yellow flags
- missing data
- required human review notes

## Risk levels

```text
GREEN  — no major flags detected in available data
YELLOW — caution / more screening needed
RED    — high-risk; professional review required
BLACK  — crisis or emergency pathway needed
```

## Hard constraints

If RED or BLACK is present, Scenario Generator must not create a normal session script.

It may only create:

- safety report;
- referral-style note;
- missing information request;
- crisis-safe message when appropriate.

## Example red/black categories

- history of psychosis;
- bipolar mania history;
- active suicidal intent;
- unstable cardiovascular condition;
- dangerous medication interaction risk;
- pregnancy flag;
- severe dissociation risk;
- inability to provide informed consent.

## Cursor implementation notes

Suggested files:

```text
src/safety/models.py
src/safety/rules.py
src/safety/engine.py
src/safety/report.py
tests/test_safety_engine.py
```

Scenario Generator must call Safety Engine output before generation.
