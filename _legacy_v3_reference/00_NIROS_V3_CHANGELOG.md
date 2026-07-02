# NIROS Research OS v3 — Changelog

Version v3 extends NIROS from a research vault into a more operational product/research architecture.

## Added in v3

- Voice-first questionnaire architecture.
- Sensor-assisted intake and session monitoring layer.
- AI problem confirmation loop: user states the problem, AI checks whether the stated problem matches the deeper profile.
- Dedicated Clinical Protocols folder.
- Dedicated Music Generation Engine folder.
- Dedicated Adaptive Session Engine folder.
- Dedicated Evidence Database folder.
- Dedicated Validation folder.
- Expanded Ethics / Safety / Explainability layer.
- NIROS SDK folder for API, schemas, prompt contracts, and LLM interfaces.
- Idea Intake system for adding new ideas in Obsidian so future AI/Cursor work can always see them.
- New templates for ideas, voice intake flows, sensor signals, and protocol specs.

## Core architectural decision

NIROS must treat the user's first stated problem as a hypothesis, not as final truth.

The system should ask:

1. What does the person say they came with?
2. What does the voice questionnaire reveal?
3. What do sensors suggest?
4. What does clinical screening allow or block?
5. What does the AI infer as the real primary therapeutic target?
6. Does the user confirm that this interpretation feels accurate?

Only after that should NIROS generate a session protocol.
