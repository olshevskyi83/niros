---
type: workflow
version: v2.0
status: active
tags: [cursor, prompting]
---

# Prompting Workflow

## Standard prompt template

```text
You are working on NIROS.

Read and follow:
- <relevant Obsidian spec files>

Task:
<exact task>

Allowed files to modify:
- <file list>

Do not modify:
- <file list>

Constraints:
- no medical claims
- no dosage/preparation content
- type hints required
- tests required

Expected output:
- <files/classes/functions>
```

## Task size

One prompt should usually create or modify one module, not the whole project.

## Review checklist

After Cursor edits:

- Did it follow the spec?
- Did it change unrelated files?
- Did it add unsafe content?
- Did it add tests?
- Does the code run?
- Is the architecture still clean?

## Recovery rule

If Cursor creates chaos, revert with Git and repeat with a smaller prompt.
