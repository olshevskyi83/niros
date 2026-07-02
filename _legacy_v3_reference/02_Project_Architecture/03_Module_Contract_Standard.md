---
type: standard
version: v2.0
status: active
tags: [niros, modules, cursor]
---

# Module Contract Standard

Every NIROS module must have a written contract.

## Required sections in every module note

```text
# Module Name

## Purpose
## Scope
## Inputs
## Outputs
## Dependencies
## Internal Logic
## Data Structures
## Safety Constraints
## Cursor Implementation Notes
## Tests
## Future Expansion
```

## Required implementation files

Each module should normally have:

```text
src/<module_name>/__init__.py
src/<module_name>/models.py
src/<module_name>/service.py
src/<module_name>/rules.py
src/<module_name>/exceptions.py
tests/test_<module_name>.py
```

Small modules may use fewer files, but no large monolithic files.

## Input/output rule

All module outputs should be serializable to JSON.

## Traceability rule

Important outputs must include a field such as:

```json
{
  "trace": {
    "input_fields": [],
    "rules_used": [],
    "evidence_items": [],
    "warnings": []
  }
}
```

## Cursor implementation notes

When asked to implement a module, Cursor must:

1. read this standard;
2. read the target module document;
3. create only the requested files;
4. add type hints;
5. add minimal tests;
6. avoid expanding scope.
