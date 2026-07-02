# Cursor Workflow

Cursor should treat this vault as the project source of truth.

## Before coding

Cursor should read:

1. `README.md`
2. `00_SYSTEM_MAP.md`
3. `.cursor/NIROS_CURSOR_CONTEXT.md`
4. `.cursor/rules/niros_rules.mdc`
5. The module overview relevant to the requested task
6. Related schema files in `12_SDK_and_API/schemas/`

## Coding rules

- Do not rename top-level modules.
- Do not implement clinical diagnosis language.
- Keep state machines explicit.
- Use schemas for module outputs.
- Add tests for safety and schema validity.
- If a new architectural decision is needed, create an ADR first.

## Recommended repo structure when code starts

```text
niros/
  app/
  src/
    interview_engine/
    hypothesis_engine/
    safety/
    schemas/
    music_engine/
    sensors/
  tests/
  docs/  # this vault or synced copy
```

## Prompt for Cursor

> Read the NIROS v4 Foundation Release. Implement only inside the current architecture. Start with the Human Understanding Engine MVP: text-based adaptive interview, explicit state machine, structured JSON output, safety checks, and tests.
