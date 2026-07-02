---
type: module-spec
version: v2.0
status: active
tags: [evidence-engine, rag, niros]
---

# Evidence Engine v2

## Purpose

The Evidence Engine retrieves, ranks, summarizes, and labels scientific evidence relevant to a participant profile, psychedelic method, clinical module, and safety report.

## Scope

The Evidence Engine does not make final clinical decisions. It produces structured evidence summaries with uncertainty and limitations.

## Inputs

- ParticipantProfile
- SafetyReport
- selected psychedelic module
- selected clinical module
- query goal
- knowledge base index

## Outputs

- EvidenceSummary
- evidence item list
- evidence quality notes
- limitations
- research gaps
- safety-relevant findings

## Evidence levels

```text
Level 5 — systematic review / meta-analysis
Level 4 — randomized controlled trial
Level 3 — prospective clinical study
Level 2 — open-label or observational study
Level 1 — case report / expert opinion / ethnography
Level 0 — speculation / unsupported claim
```

## Internal logic

1. Build search query from profile + method + module.
2. Retrieve candidate passages from RAG.
3. Filter by source metadata.
4. Rank by relevance and evidence level.
5. Summarize findings.
6. Mark uncertainty.
7. Output structured EvidenceSummary.

## Safety constraints

The Evidence Engine must not convert evidence into dosing or preparation instructions.

## Cursor implementation notes

Suggested files:

```text
src/evidence/models.py
src/evidence/service.py
src/evidence/ranking.py
src/evidence/summarizer.py
src/evidence/prompts.py
tests/test_evidence_engine.py
```

Core classes:

```text
EvidenceEngine
EvidenceRetriever
EvidenceRanker
EvidenceSummaryBuilder
```
