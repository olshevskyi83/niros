# ADR-003 — Adaptive Interview State Machine

## Status

Accepted

## Context

A free-form chatbot is unsafe and hard to validate.

## Decision

Use an explicit state machine. AI may generate natural language and extract signals, but state transitions are controlled.

## Consequences

- Easier testing.
- Lower cost.
- Better safety.
- Cursor can implement deterministic logic around AI calls.
