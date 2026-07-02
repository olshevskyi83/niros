---
title: System Architecture Map
project: NeuroIcaro Research Platform
status: draft
tags: [neuroicaro]
---

# System Architecture Map

## High-level architecture

```mermaid
flowchart TD
    U[User / Participant] --> Q[Questionnaire System]
    U --> V[Voice Interview]
    U --> P[Physiology Layer]
    Q --> PE[Profile Engine]
    V --> PE
    P --> PE
    PE --> TS[Therapeutic Target Selector]
    RAG[Research RAG] --> TS
    TS --> SG[Script Generator]
    SG --> CE[Composer Engine]
    CE --> AE[Audio / Voice Engine]
    AE --> SP[Session Protocol]
    SP --> OM[Outcome Measurement]
    OM --> AN[Analytics]
    AN --> PE
```

## Key subsystems

- [[05_Profile_Engine/Profile Engine Overview]]
- [[06_Questionnaire_System/Questionnaire Overview]]
- [[07_Voice_and_Speech_Analysis/Voice Analysis Overview]]
- [[08_Physiology_Layer/Physiology Layer Overview]]
- [[04_Research_RAG/RAG System Overview]]
- [[11_NeuroIcaro_Composer/Composer Overview]]
- [[13_Session_Engine/Session Protocol Overview]]
