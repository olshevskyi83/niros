---
type: development-guide
version: v2.0
status: active
tags: [cursor, development, niros]
---

# Cursor Master Guide

Cursor is the coding assistant for NIROS. It is not the architect.

## Operating model

```text
Obsidian = source of truth
Founder = product owner
ChatGPT = architecture/design assistant
Cursor = implementation assistant
Git = history and rollback
```

## Before using Cursor

1. Open the relevant Obsidian module note.
2. Read the Cursor Implementation Notes section.
3. Decide the exact task.
4. Ask Cursor to modify only specific files.
5. Run tests.
6. Commit.

## Never prompt Cursor like this

```text
Build NIROS.
Create the whole app.
Implement all modules.
Make it production ready.
```

## Good prompt shape

```text
Read these files:
- docs/...
- modules/...

Task:
Implement only src/safety/models.py and src/safety/engine.py.

Constraints:
- no UI changes
- no dosing or substance-preparation content
- type hints required
- add tests in tests/test_safety_engine.py
```

## Development sequence

1. Project structure.
2. Configuration.
3. Schemas.
4. Module JSON files.
5. Profile Engine.
6. Safety Engine.
7. Evidence Engine.
8. Scenario Generator.
9. Streamlit UI.
10. Timeline Engine.
11. Outcome Tracker.

## Cursor rule

If Cursor wants to change architecture, stop and update Obsidian first.
