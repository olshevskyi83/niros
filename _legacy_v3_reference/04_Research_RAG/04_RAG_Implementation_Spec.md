---
type: implementation-spec
version: v2.0
status: active
tags: [rag, implementation, cursor]
---

# RAG Implementation Spec

## MVP stack

- Python
- ChromaDB
- local folder-based knowledge base
- optional OpenAI embeddings or local embeddings
- Markdown evidence summaries

## Required functions

```python
load_document(path: str) -> Document
chunk_document(document: Document) -> list[DocumentChunk]
embed_chunks(chunks: list[DocumentChunk]) -> None
search(query: str, filters: dict | None = None) -> list[SearchResult]
build_evidence_summary(results: list[SearchResult]) -> EvidenceSummary
```

## Filters

Search must support filters:

- psychedelic method;
- clinical module;
- source type;
- evidence level;
- safety tag;
- year range;
- review status.

## Output requirement

RAG results must include source metadata. Never return text snippets without source identity.

## Cursor implementation notes

Keep RAG separate from Scenario Generator. Scenario Generator receives an EvidenceSummary, not raw vector search results.
