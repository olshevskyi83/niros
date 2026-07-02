---
type: module-spec
version: v2.0
status: active
tags: [profile-engine, niros]
---

# Profile Engine v2

## Purpose

The Profile Engine converts questionnaire responses into a structured participant profile that other modules can use.

## Inputs

- QuestionnaireResponse
- optional facilitator notes
- optional previous session history

## Outputs

- ParticipantProfile
- profile summary
- triggers list
- worldview profile
- voice/music preferences
- clinical direction candidates
- method compatibility notes

## Key profile domains

```text
basic_context
clinical_focus
psychological_profile
worldview
trauma_sensitivity
control_and_agency
body_relationship
music_profile
voice_profile
language_profile
risk_relevant_features
integration_goals
```

## Internal logic

1. Validate questionnaire response.
2. Normalize answers.
3. Score profile dimensions.
4. Extract safety-relevant fields.
5. Generate structured profile object.
6. Generate human-readable profile summary.

## Safety constraints

The Profile Engine does not approve a session. It only prepares data for the Safety Engine.

## Cursor implementation notes

Suggested files:

```text
src/profile/models.py
src/profile/builder.py
src/profile/scoring.py
src/profile/summary.py
tests/test_profile_engine.py
```

Core classes:

```text
ProfileEngine
ProfileBuilder
ProfileValidator
ProfileSummarizer
```
