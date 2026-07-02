---
type: cursor-rules
version: v2.0
status: active
tags: [cursor, rules]
---

# Cursor Rules for NIROS

These rules should be copied into Cursor project rules or `.cursor/rules`.

## General rules

- Follow the Obsidian specification.
- Do not invent architecture.
- Do not create monolithic files.
- Use type hints.
- Prefer dataclasses or Pydantic models for structured data.
- Keep business logic out of Streamlit pages.
- Write small functions.
- Add tests for core logic.
- Use clear names.

## Safety rules

- Do not generate dosage advice.
- Do not generate substance preparation instructions.
- Do not generate extraction or synthesis instructions.
- Do not claim treatment or cure.
- Safety Engine must run before Scenario Generator.
- RED/BLACK safety reports must block normal scenario generation.

## Architecture rules

- UI calls services.
- Services call engines.
- Engines use schemas and storage.
- Modules communicate through typed objects.
- Outputs must be JSON-serializable.
- Important outputs must include trace metadata.

## File-size rule

If a file grows beyond about 300 lines, propose splitting it.

## Cursor behavior rule

When uncertain, ask for clarification or create a minimal safe implementation. Do not guess clinical logic.
