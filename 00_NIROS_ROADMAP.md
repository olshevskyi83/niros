# NIROS Roadmap

## Status dashboard

| Phase |                    Name | Status  | Goal                                       |
| ----- | ----------------------: | ------- | ------------------------------------------ |
| 0     |  Research OS Foundation | Stable  | Freeze architecture and rules              |
| 1     | Human Understanding MVP | Next    | Text interview + structured profile        |
| 2     |     Voice Interview MVP | Planned | Speech-to-text and text-to-speech layer    |
| 3     |    AI Hypothesis Engine | Planned | Declared vs confirmed problem logic        |
| 4     |            Safety Layer | Planned | Risk screen, escalation, contraindications |
| 5     |      Therapeutic Engine | Planned | Target-based session planning              |
| 6     |            Music Engine | Planned | Music objectives, prompts, session blocks  |
| 7     |                 Sensors | Later   | HRV, EDA, sleep, voice features            |
| 8     |              Validation | Ongoing | Compare outputs against expert review      |

## Roadmap graphic

```mermaid
gantt
    title NIROS Foundation Roadmap
    dateFormat  YYYY-MM-DD
    section Foundation
    Vault Architecture Freeze       :done,    f1, 2026-06-30, 2d
    Cursor Context                   :done,    f2, 2026-06-30, 2d
    section MVP
    Text Adaptive Interview          :active,  m1, 2026-07-02, 14d
    Structured Profile JSON          :         m2, after m1, 7d
    Safety Screen                    :         m3, after m2, 7d
    section Next
    Voice Layer                      :         n1, after m3, 14d
    Therapeutic Planner              :         n2, after n1, 21d
    Music Engine Prototype           :         n3, after n2, 21d
```

## Anti-NASA rule

The project must not expand every time a new interesting idea appears. New ideas enter [[19_Inbox/00_Capture_Rules]] and are reviewed before they can change the permanent architecture.
