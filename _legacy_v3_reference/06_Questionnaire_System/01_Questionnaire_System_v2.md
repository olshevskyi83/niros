---
type: module-spec
version: v2.0
status: active
tags: [questionnaire, intake, niros]
---

# Questionnaire System v2

## Purpose

Collect structured data for profile generation, safety screening, module selection, and personalization.

## Design principle

The questionnaire must be modular. The user should not face all possible questions at once.

## Core blocks

```text
1_basic_intake
2_medical_safety
3_psychological_profile
4_worldview_and_symbolic_language
5_music_voice_language
6_psychedelic_history
7_clinical_module_specific
8_integration_goals
```

## MVP target

First version: 80–120 questions total, with conditional branching.

## Output

```json
{
  "response_id": "",
  "created_at": "",
  "blocks_completed": [],
  "answers": {},
  "missing_required_fields": [],
  "completion_status": "draft"
}
```

## Cursor implementation notes

Start with JSON questionnaire definitions. Do not hardcode questions directly in Streamlit.

Suggested files:

```text
modules/questionnaires/intake_v1.json
src/questionnaire/models.py
src/questionnaire/loader.py
src/questionnaire/validator.py
app/pages/01_Intake.py
```
