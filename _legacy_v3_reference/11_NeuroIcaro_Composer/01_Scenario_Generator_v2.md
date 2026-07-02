---
type: module-spec
version: v2.0
status: active
tags: [scenario-generator, composer, niros]
---

# Scenario Generator v2

## Purpose

Generate personalized session-support materials from profile, safety report, evidence summary, and module rules.

## Inputs

- ParticipantProfile
- SafetyReport
- EvidenceSummary
- PsychedelicModule
- ClinicalModule
- VoiceProfile
- MusicProfile

## Outputs

- session_script.md
- facilitator_notes.md
- integration_plan.md
- risk_notes.md
- trace metadata

## Scenario structure

```text
1. Preparation notes
2. Opening
3. Grounding
4. Trust building
5. Main therapeutic arc
6. Silence periods
7. Peak support phrases
8. Difficult experience support
9. Return phase
10. Closing
11. Integration plan
```

## Generation rules

- No dosage.
- No substance preparation.
- No claims of cure.
- No coercive language.
- No worldview imposition.
- No trauma-forcing language.
- Respect safety flags.
- Include uncertainty and facilitator review notes.

## Cursor implementation notes

Suggested files:

```text
src/generation/scenario_models.py
src/generation/scenario_generator.py
src/generation/prompts.py
src/generation/validators.py
tests/test_scenario_generator.py
```

Scenario generation must fail safely if SafetyReport is missing.
