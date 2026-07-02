# First Contact

First contact defines the user's initial experience and sets boundaries before any deep assessment.

## Goals

- Establish consent.
- Explain what NIROS can and cannot do.
- Capture the person's declared reason for coming.
- Avoid overpromising.
- Start safety screening gently.

## Example opening flow

```mermaid
sequenceDiagram
    participant User
    participant NIROS
    NIROS->>User: What brings you here today?
    User->>NIROS: I think I have depression.
    NIROS->>User: I can help explore what is happening, but I won't diagnose. We will clarify the main difficulty together.
    NIROS->>User: Is it okay if I ask a few questions to understand the situation better?
```

## Required fields

- consent_status
- declared_problem_text
- preferred_language
- urgency_level
- safety_warning_present
