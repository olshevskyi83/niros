# Markdown Ontology Vault

Obsidian-style vault for the NIROS master ontology. When this directory contains
`.md` files, `OntologyContext` loads them alongside the JSON seed data in
`knowledge_library/master_ontology/`.

Expected layout:

- `01 Presenting Concerns/*.md`
- `02 Mechanisms/**/*.md`
- `03 Therapeutic Change Processes/**/*.md`

Each file uses YAML frontmatter (`id`, `type`, `status`, etc.) and Markdown section
headings (`## Short Definition`, `## How It Is Maintained`, ...).

Draft and incomplete files are valid. The compiler must not require completeness.
