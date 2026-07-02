# Psychedelic-Assisted Therapy Notes

This document stores high-level scientific and product architecture notes. It must not become a dosing manual or unsupervised-use guide.

## Relevant domains

- Preparation
- Screening and contraindications
- Set and setting
- Therapeutic alliance
- Music and emotional arc
- Integration
- Adverse event monitoring

## NIROS stance

NIROS should focus on:

1. Structured preparation.
2. Risk screening.
3. Human understanding.
4. Integration support.
5. Research documentation.

It should not autonomously recommend substance use or replace licensed supervision.

## Architecture implication

```mermaid
flowchart TD
    Intake[Human Understanding Engine] --> Risk[Risk + Contraindications]
    Risk -->|High risk| Review[Human/clinical review]
    Risk -->|Acceptable risk| Prep[Preparation support]
    Prep --> Session[Session support architecture]
    Session --> Integration[Integration support]
```
