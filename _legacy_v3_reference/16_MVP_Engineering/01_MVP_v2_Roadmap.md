---
type: roadmap
version: v2.0
status: active
tags: [mvp, roadmap, niros]
---

# MVP v2 Roadmap

## Goal

Build a local-first prototype that proves the core NIROS flow works.

## MVP flow

```text
questionnaire → profile → safety report → module selection → evidence summary → safe scenario draft → export
```

## MVP modules

- Questionnaire System
- Profile Engine
- Safety Engine
- Psilocybin Module
- Depression Module
- Anxiety Module
- Fibromyalgia / Chronic Pain Module
- Basic Evidence Engine
- Scenario Generator
- Export system

## Phase 1 — Skeleton

- repository structure;
- config;
- schemas;
- module JSON files;
- demo data.

## Phase 2 — Core logic

- questionnaire validation;
- profile builder;
- safety risk scoring;
- module selector.

## Phase 3 — Knowledge base

- markdown/PDF loader;
- chunking;
- metadata;
- simple search;
- evidence summary.

## Phase 4 — Generation

- safe prompt templates;
- scenario draft;
- facilitator notes;
- integration plan;
- trace metadata.

## Phase 5 — UI

- Streamlit dashboard;
- intake page;
- profile page;
- safety report page;
- evidence page;
- scenario export page.

## Phase 6 — Hardening

- tests;
- unsafe-output validator;
- Git workflow;
- Docker.

## Not in MVP

- real-time EEG;
- live session recorder;
- ayahuasca/DMT module implementation;
- advanced ML;
- mobile app;
- public deployment.
