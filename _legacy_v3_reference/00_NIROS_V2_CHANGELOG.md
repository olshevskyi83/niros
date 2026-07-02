---
type: changelog
version: v2.0
status: active
tags: [changelog, niros]
---

# NIROS v2 Changelog

## Major changes

- Project renamed internally from NeuroIcaro to **NIROS**.
- NeuroIcaro remains a public/legacy name.
- Vault converted from notes to operating specification.
- Added Cursor-ready development system.
- Added Safety Engine v2.
- Added Evidence Engine v2.
- Added Psychedelic Modules folder.
- Added Clinical Modules folder.
- Added Timeline Engine v2.
- Added Research OS layer.
- Added module contract standard.
- Added traceability model.

## Architectural shift

Old emphasis:

```text
Profile → Composer → Voice
```

New emphasis:

```text
Knowledge Base → Evidence Engine → Safety Engine → Profile Engine → Modules → Scenario/Voice/Music → Timeline → Outcomes
```

## Implementation principle

Cursor should now treat this vault as a specification, not as general notes.
