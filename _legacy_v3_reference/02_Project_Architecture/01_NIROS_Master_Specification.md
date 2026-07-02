---
type: master-specification
version: v2.0
status: active
tags: [niros, architecture, cursor]
---

# NIROS Master Specification

This is the central specification for NIROS. Cursor and future developers should read this document before implementing any code.

## Mission

Build a local-first research operating system for personalized psychedelic session support.

## Primary system equation

```text
psychedelic method
+ clinical/research direction
+ participant profile
+ safety constraints
+ scientific evidence
+ voice/music/script personalization
+ synchronized timeline data
+ follow-up outcomes
= individual session-support research model
```

## Core modules

```text
NIROS Core
├── Questionnaire System
├── Profile Engine
├── Safety Engine
├── Knowledge Base
├── Evidence Engine
├── Psychedelic Modules
├── Clinical Modules
├── Scenario Generator
├── Voice Engine
├── Music Engine
├── Timeline Engine
├── Physiology Layer
├── Outcome Analytics
├── Research OS
└── Cursor Development System
```

## Required build order

1. Create repository and folder structure.
2. Add project configuration.
3. Add module JSON files.
4. Implement questionnaire schema.
5. Implement Profile Engine.
6. Implement Safety Engine.
7. Implement local storage.
8. Implement Knowledge Base loader.
9. Implement Evidence Engine.
10. Implement Scenario Generator.
11. Implement Streamlit UI.
12. Implement Timeline Engine.
13. Implement Outcome Tracker.
14. Add tests.
15. Add Docker.

## First MVP scope

MVP v2.0 includes:

- local Streamlit app;
- demo profiles;
- psilocybin module;
- depression, anxiety, fibromyalgia/chronic pain modules;
- questionnaire;
- profile generation;
- safety report;
- evidence summary from local markdown/PDF knowledge base;
- session script generation without dosing or substance instructions;
- export to Markdown and JSON.

## Design constraints

- Python-first.
- Local-first.
- Modular.
- Type-hinted.
- Testable.
- No monolithic files.
- No medical claims.
- No dosage/preparation content.
- Human review required for any real-world use.

## Data principle

Every generated output must preserve a trace:

```text
input answers → profile features → safety flags → evidence snippets → module rules → generated output
```

## Naming principle

Use **NIROS** for the system and architecture. Use **NeuroIcaro** only where public-facing product language is needed.

## Cursor implementation notes

Cursor must not invent new architecture. Cursor should implement only the module currently specified.

Before coding, Cursor should read:

- [[28_Cursor_Development/01_Cursor_Master_Guide]]
- [[28_Cursor_Development/02_Cursor_Rules_for_NIROS]]
- [[02_Project_Architecture/03_Module_Contract_Standard]]
- the target module specification.
