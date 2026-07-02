# SDK and API Overview

This module defines stable interfaces for code implementation.

## Core objects

- HumanProfile
- InterviewState
- HypothesisSet
- RiskAssessment
- SensorSnapshot
- SessionPlan
- MusicBrief

## API flow

```mermaid
sequenceDiagram
    participant App
    participant InterviewAPI
    participant AI
    participant DB
    App->>InterviewAPI: user answer
    InterviewAPI->>AI: extract + next action
    AI->>InterviewAPI: structured output
    InterviewAPI->>DB: save state
    InterviewAPI->>App: next question + state
```
