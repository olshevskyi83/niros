---
type: pipeline-spec
version: v2.0
status: active
tags: [papers, ingestion, rag]
---

# Paper Ingestion Pipeline

## Purpose

Convert downloaded or manually added research papers into searchable, tagged, evidence-scored knowledge base entries.

## Pipeline

```text
PDF / Markdown / TXT
        ↓
Text extraction
        ↓
Metadata extraction
        ↓
Chunking
        ↓
Embedding
        ↓
Vector storage
        ↓
Evidence metadata storage
        ↓
Manual review status
```

## Chunking rules

- Preserve title, abstract, headings, and conclusion when possible.
- Keep chunks small enough for retrieval but large enough for context.
- Store source document ID and page/section if available.

## Review statuses

```text
unreviewed
machine_summarized
human_reviewed
rejected
archived
```

## Cursor implementation notes

Use a simple MVP first:

- load PDF or markdown;
- extract text;
- chunk text;
- save chunks to ChromaDB;
- save metadata JSON.

Do not implement automatic quality scoring until metadata extraction works.
