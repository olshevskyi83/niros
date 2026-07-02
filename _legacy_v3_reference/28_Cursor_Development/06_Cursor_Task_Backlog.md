# Cursor Task Backlog

Use this file for implementation-ready tasks.

## Format

```markdown
## TASK-ID — Task title

### Goal

### Files/modules affected

### Inputs

### Outputs

### Acceptance criteria

### Safety constraints
```

## Initial v3 implementation tasks

## NIROS-V3-001 — Implement voice-first intake schema

### Goal
Create backend schema for voice questionnaire answers.

### Files/modules affected
- intake API
- database schema
- profile engine

### Inputs
- transcript
- question id
- structured extraction
- confidence
- safety flags

### Outputs
- VoiceAnswer object

### Acceptance criteria
- raw transcript preserved
- structured fields extracted
- confidence stored
- safety flags stored

### Safety constraints
Voice biomarkers cannot be used as diagnosis or lie detection.

---

## NIROS-V3-002 — Implement declared problem confirmation flow

### Goal
Build the flow from declared problem to confirmed therapeutic target.

### Files/modules affected
- questionnaire engine
- profile engine
- clinical modules
- session generator

### Inputs
- declared problem
- questionnaire summary
- sensor context
- safety flags

### Outputs
- confirmed therapeutic target
- explanation for user

### Acceptance criteria
- user can confirm, partially confirm, reject, or restate
- no final protocol generated before confirmation or review

### Safety constraints
High-risk states route to human review.
