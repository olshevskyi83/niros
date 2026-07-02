# Declared Problem Confirmation Loop

## Purpose

The system must not simply accept the user's first label.

A person may say "anxiety" but the real working target may be trauma activation, loss of control, chronic stress, social fear, body panic, or existential uncertainty.

## Core loop

```text
User declares problem
  ↓
AI asks clarifying questions
  ↓
AI compares answers with clinical modules
  ↓
AI detects likely primary pattern
  ↓
AI explains interpretation to user
  ↓
User confirms / rejects / edits
  ↓
System creates confirmed target
```

## Example

User says:

> I came because I have anxiety.

AI interpretation:

> You described anxiety, but the strongest pattern seems to be fear of losing control in the body, especially when physical sensations appear. This may be closer to panic-style body threat sensitivity than general anxiety. Does that feel accurate?

User options:

- Yes, accurate.
- Partly accurate.
- No, wrong.
- I want to explain differently.

## Confirmation states

- `confirmed`
- `partially_confirmed`
- `rejected`
- `unclear`
- `requires_human_review`

## Safety rule

If severe depression, psychosis risk, mania risk, suicidality, medical instability, or contraindications appear, NIROS must stop personalization and move into safety guidance / human review pathway.

## Output object

```json
{
  "declared_problem": "anxiety",
  "candidate_targets": [
    "panic/body threat sensitivity",
    "loss of control fear",
    "chronic stress physiology"
  ],
  "ai_summary": "The strongest pattern appears to be...",
  "user_confirmation_state": "partially_confirmed",
  "confirmed_target": "panic-linked body threat sensitivity",
  "safety_flags": []
}
```
