# NIROS Cursor Context

You are working inside NIROS Research OS v4 Foundation Release.

## Read first

1. `README.md`
2. `00_SYSTEM_MAP.md`
3. `00_NIROS_ROADMAP.md`
4. `01_Vision/01_NIROS_Design_Principles.md`
5. `04_Human_Understanding_Engine/00_HUE_Overview.md`
6. `16_Development/01_Cursor_Workflow.md`

## Architecture freeze

Do not rename top-level folders. Do not invent new top-level modules unless the user explicitly asks and an ADR is created.

## First implementation target

Human Understanding Engine MVP:

- text-based interview
- explicit state machine
- question library
- structured extraction
- risk screen
- declared vs confirmed problem logic
- final HumanProfile JSON

## Safety rules

- No diagnosis claims.
- No autonomous medical instruction.
- Risk checks interrupt normal flow.
- Sensor data is supportive only.
- All important outputs should be explainable.

## Coding style

- Prefer small modules.
- Prefer typed data models / schemas.
- Add tests for every state transition.
- Add schema validation for AI outputs.
- Keep prompt contracts in versioned files.
