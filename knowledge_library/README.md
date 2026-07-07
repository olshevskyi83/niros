# NIROS Knowledge Library

This is the canonical source library for NIROS knowledge compilation.

Only clean, human-verified `.txt` files belong here. PDF, EPUB, OCR output
processing, scanned-page handling, and other document conversion steps happen
outside NIROS before files enter this tree.

Future Knowledge Compiler flow:

```text
External OCR / text preparation
  -> clean TXT
  -> knowledge_library/
  -> RawSourceCorpus
  -> Semantic Extraction
  -> Human Review
  -> domain-specific CTPC
  -> Runtime adapters
```

Do not flatten source families. Domain and family folders are part of source
provenance and later CTPC separation.
