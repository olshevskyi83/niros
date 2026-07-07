# Legacy TLE Corpus Upload Structure

This directory is **legacy storage only**.

From Sprint 030 / Slice 4 onward, NIROS does not read books or source material
from `niros_tle/corpus/`. All new knowledge-source TXT files belong in the
canonical `knowledge_library/` tree. OCR/PDF/EPUB conversion happens outside
NIROS, and NIROS receives only clean, human-verified TXT files.

This directory holds therapeutic language **source material** for future TLE ingestion. Nothing here is processed automatically in the current sprint.

## Layout

Each source family has three subfolders:

```
corpus/<source_family>/
    raw/         Original uploads (PDF, TXT, MD, EPUB, …)
    processed/   Cleaned / chunked / normalized artifacts (empty until ingestion exists)
    metadata/    Per-source metadata only — no copyrighted text
```

## How to use (future)

1. Place source files in `corpus/<source_family>/raw/`.
2. Do **not** manually edit `processed/` — that folder will be populated by the ingestion pipeline later.
3. Use `metadata/` for source registry entries, license notes, and upload records — not book text.

## Current status

- No books are ingested in this slice.
- No PDF parsing, embeddings, RAG, or LLM calls.
- See `../metadata/corpus_manifest.json` for the canonical list of source families and paths.

## Source families

Psychotherapy: `erickson`, `act`, `ifs`, `cft`, `narrative`, `motivational_interviewing`

Indigenous healing (reference metadata): `maria_sabina`, `shipibo`, `quechua`
