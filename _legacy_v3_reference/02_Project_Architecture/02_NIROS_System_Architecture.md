---
type: architecture
version: v2.0
status: active
tags: [niros, architecture]
---

# NIROS System Architecture

## High-level flow

```text
Participant Intake
        ↓
Questionnaire System
        ↓
Profile Engine
        ↓
Safety Engine
        ↓
Method + Clinical Module Selection
        ↓
Knowledge Base / RAG
        ↓
Evidence Engine
        ↓
Scenario Generator
        ↓
Voice Engine + Music Engine
        ↓
Session Timeline Engine
        ↓
Outcome Tracker
        ↓
Research Analytics
```

## Core design pattern

Each module must work independently and communicate through typed objects or JSON-compatible dictionaries.

## Module categories

### Input modules

- Questionnaire System
- Document Loader
- Manual facilitator notes
- Physiology import

### Reasoning modules

- Profile Engine
- Safety Engine
- Evidence Engine
- Module Selector

### Generation modules

- Scenario Generator
- Voice Engine
- Music Guidance Engine
- Integration Plan Generator

### Logging modules

- Timeline Engine
- Session Event Logger
- Adverse Event Logger

### Analytics modules

- Outcome Tracker
- Research Dashboard
- Cohort Comparison

## Recommended Python package structure

```text
src/
├── config.py
├── schemas/
├── storage/
├── questionnaire/
├── profile/
├── safety/
├── knowledge/
├── evidence/
├── modules/
├── generation/
├── timeline/
├── outcomes/
├── reports/
└── utils/
```

## UI architecture

Use Streamlit for MVP.

```text
app/
├── dashboard.py
└── pages/
    ├── 01_Intake.py
    ├── 02_Profile.py
    ├── 03_Safety.py
    ├── 04_Evidence.py
    ├── 05_Scenario.py
    ├── 06_Timeline.py
    ├── 07_Outcomes.py
    └── 08_Knowledge_Base.py
```

## Dependency direction

UI depends on business logic. Business logic must not depend on UI.

```text
Streamlit UI → service layer → core engines → schemas/storage
```

## Cursor implementation notes

Do not place business logic inside Streamlit pages. Streamlit pages should only collect inputs, call services, and display results.
