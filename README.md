# NIROS Research OS v4 — Foundation Release

> [!IMPORTANT]
> **Archived research prototype — July 2026**
>
> Active development of NIROS has stopped. The project explored whether a
> structured psychological intake and evidence-informed personalization system
> could support the creation of short therapeutic vocal patterns for
> psychedelic contexts.
>
> The central hypothesis was not validated. In particular, the project did not
> establish that its psychological inferences were clinically reliable or that
> personalized vocal patterns were safe or therapeutically effective during
> psychedelic experiences. The software must not be used for diagnosis,
> treatment, crisis support, psychedelic-session guidance, or autonomous
> psychological intervention.
>
> The repository is preserved as a research and engineering record. Its
> architectures, tests, ontologies, scores, and generated outputs should not be
> interpreted as clinical evidence.

**NIROS** is a research operating system for building an adaptive human-understanding and therapeutic-support platform.

This vault is designed for two audiences:

1. **Humans in Obsidian** — clear navigation, diagrams, dashboards, templates, and stable conceptual language.
2. **Cursor / AI coding agents** — stable folder names, machine-readable context, architecture rules, module boundaries, schemas, and development workflow.

## Foundation rule

This release freezes the top-level architecture. Future work should add or refine documents inside existing modules, not rename the module structure unless a formal ADR approves the change.

## Start here

- [[00_HOME]] — human dashboard
- [[00_INDEX]] — full vault index
- [[00_SYSTEM_MAP]] — architecture map
- [[00_NIROS_ROADMAP]] — execution roadmap
- [[01_Vision/01_NIROS_Design_Principles]] — permanent design rules
- [[16_Development/01_Cursor_Workflow]] — how Cursor should use this vault
- [[19_Inbox/00_Capture_Rules]] — how new ideas enter the system

## Core pipeline

```mermaid
flowchart LR
    A[New idea] --> B[19_Inbox]
    B --> C[20_Workbench]
    C --> D[Review]
    D --> E[Permanent module docs]
    E --> F[Cursor implementation]
    F --> G[Validation]
```
