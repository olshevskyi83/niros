---
type: architecture
version: v2.0
status: active
tags: [traceability, evidence, niros]
---

# Traceability Model

Traceability is one of the most important NIROS principles.

## Why traceability matters

Without traceability, AI outputs become unreviewable. NIROS must be able to explain why a script, warning, or recommendation was produced.

## Trace chain

```text
participant answers
→ profile features
→ safety flags
→ selected module rules
→ evidence items
→ generation prompt
→ generated output
→ facilitator edits
→ session events
→ follow-up outcomes
```

## Required trace fields

Every major output should include:

```json
{
  "trace_id": "",
  "created_at": "",
  "source_profile_id": "",
  "source_safety_report_id": "",
  "evidence_item_ids": [],
  "module_ids": [],
  "generator_version": "",
  "human_review_status": "not_reviewed"
}
```

## Human review statuses

```text
not_reviewed
reviewed
edited_by_facilitator
rejected
archived
```

## Cursor implementation notes

Do not create generation outputs without trace metadata.
