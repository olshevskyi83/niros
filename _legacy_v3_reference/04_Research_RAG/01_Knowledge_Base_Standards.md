---
type: knowledge-base-standard
version: v2.0
status: active
tags: [rag, evidence, knowledge-base]
---

# Knowledge Base Standards

The NIROS knowledge base stores scientific and contextual material used by the Evidence Engine.

## Source priority

Preferred sources:

- open-access journal articles;
- PubMed Central full texts;
- PubMed abstracts where full text is unavailable;
- clinical trial registry entries;
- open preprints clearly marked as preprints;
- books or ethnographic material only when legally available.

## Source categories

```text
psychedelic_research
clinical_condition
safety
music_brain
voice_psychology
physiology
timeline_methods
integration
anthropology
legal_ethics
```

## Folder structure

```text
knowledge_base/
├── psilocybin/
├── ayahuasca_dmt/
├── depression/
├── anxiety/
├── ptsd/
├── addiction/
├── ocd/
├── fibromyalgia_pain/
├── music_brain/
├── voice_psychology/
├── safety/
├── integration/
└── anthropology/
```

## Metadata fields

```json
{
  "paper_id": "",
  "title": "",
  "authors": [],
  "year": "",
  "doi": "",
  "source_url": "",
  "source_type": "",
  "module_tags": [],
  "psychedelic": "",
  "condition": "",
  "study_type": "",
  "sample_size": null,
  "main_findings": "",
  "limitations": "",
  "safety_notes": "",
  "evidence_level": 0,
  "review_status": "unreviewed"
}
```

## Cursor implementation notes

The document loader must store metadata separately from embeddings. Never rely on embeddings alone.
