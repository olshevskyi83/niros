---
type: architecture
version: v2.0
status: active
tags: [data-flow, niros]
---

# Data Flow v2

## Main data objects

```text
QuestionnaireResponse
ParticipantProfile
SafetyReport
ModuleSelection
EvidenceSummary
ScenarioScript
VoiceTimeline
MusicGuidance
SessionTimeline
OutcomeAssessment
ResearchReport
```

## Flow

```text
QuestionnaireResponse
        ↓
ParticipantProfile
        ↓
SafetyReport
        ↓
ModuleSelection
        ↓
EvidenceSummary
        ↓
ScenarioScript + VoiceTimeline + MusicGuidance
        ↓
SessionTimeline
        ↓
OutcomeAssessment
        ↓
ResearchReport
```

## Storage format for MVP

- JSON for structured objects.
- Markdown for human-readable reports.
- SQLite for relational session data.
- ChromaDB for local vector search.

## Production direction

- PostgreSQL for core data.
- Qdrant for vector search.
- Object storage for audio and physiological streams.

## Data privacy principle

Participant data must be separated from research metadata whenever possible.

## Cursor implementation notes

Create schemas before UI. The UI must not invent new fields that are not defined in schemas.
