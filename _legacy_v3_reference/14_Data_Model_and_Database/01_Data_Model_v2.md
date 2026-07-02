---
type: data-model
version: v2.0
status: active
tags: [database, schemas, niros]
---

# Data Model v2

## MVP storage

Use a hybrid local approach:

- JSON for structured profiles and reports;
- Markdown for readable exports;
- SQLite for session/index data;
- ChromaDB for vector search.

## Main entities

```text
Participant
QuestionnaireResponse
ParticipantProfile
SafetyReport
PsychedelicModule
ClinicalModule
EvidenceItem
EvidenceSummary
ScenarioScript
VoiceTimeline
MusicGuidance
SessionTimeline
SessionEvent
OutcomeAssessment
AdverseEvent
```

## Core tables for SQLite

```text
participants
questionnaire_responses
profiles
safety_reports
sessions
session_events
outcome_assessments
adverse_events
evidence_items
generated_reports
```

## Export files

```text
reports/<participant_id>/profile.json
reports/<participant_id>/safety_report.md
reports/<participant_id>/evidence_summary.md
reports/<participant_id>/session_script.md
reports/<participant_id>/integration_plan.md
```

## Cursor implementation notes

Start with Pydantic schemas before SQLAlchemy. Database can be added after the data objects are stable.
