# NIROS TLE — Therapeutic Language Engine (R&D Workspace)

This directory is a **separate research and development workspace** for the Therapeutic Language Engine (TLE). It is not part of the NIROS Core MVP runtime.

## What TLE is

TLE analyzes therapeutic language sources (psychotherapy traditions, indigenous healing lineages, and related corpora) and exports **structured Universal Therapeutic Patterns** — descriptive metadata about language patterns, not generated therapeutic text.

## What TLE is not

- TLE does **not** replace NIROS Core.
- TLE does **not** choose which pattern fits a person.
- TLE does **not** generate final personalized Icaros.

Person–pattern compatibility is decided by **NIROS Core** (Human Digital Fingerprint, Semantic Signal Graph, and Pattern-Person Fit). TLE supplies candidate pattern definitions; NIROS Core evaluates fit.

## Workspace layout

```
niros_tle/
    corpus/           Source-family folders (no ingested text yet)
    patterns/         Seed Universal Therapeutic Patterns (structured JSON)
    pattern_contract.py  TLE import/export validation and Core conversion
    embeddings/       Reserved for future embedding artifacts
    metadata/         Corpus source registry (ids, status, notes)
    exports/          Reserved for TLE pattern export outputs
    tests/            Workspace structure and schema validation
```

## Current status

Placeholder only. No corpus ingestion, embeddings, RAG, or LLM calls are implemented in this sprint.

Seed patterns can be exported to Core-compatible JSON:

```bash
python -c "from niros_tle.pattern_contract import DEFAULT_SEED_PATTERNS_PATH, DEFAULT_CORE_EXPORT_PATH, export_core_patterns, load_tle_patterns; export_core_patterns(load_tle_patterns(DEFAULT_SEED_PATTERNS_PATH), DEFAULT_CORE_EXPORT_PATH)"
```

## Relationship to NIROS Core

TLE is **independent** of NIROS Core. Nothing in `niros/` imports from `niros_tle/` yet. When TLE exports are ready, they can be reviewed and optionally promoted into NIROS knowledge libraries — that integration is future work.
