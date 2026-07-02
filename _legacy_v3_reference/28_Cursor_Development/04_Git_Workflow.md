---
type: workflow
version: v2.0
status: active
tags: [git, cursor, development]
---

# Git Workflow

## Branch strategy for MVP

```text
main        stable working state
dev         active integration
feature/*   individual module tasks
```

For solo development, `main` + frequent commits is acceptable at first.

## Commit rhythm

Commit after every successful small task.

Examples:

```text
init project structure
add config module
add questionnaire schema
add profile engine models
implement safety gate rules
add psilocybin module json
add streamlit intake page
```

## Before commit

- run tests;
- run app if UI changed;
- check unsafe content;
- update Obsidian spec if architecture changed.

## Commit message format

```text
<area>: <short description>
```

Examples:

```text
safety: add risk level model
profile: implement profile builder
rag: add document chunking
ui: add intake page
```
