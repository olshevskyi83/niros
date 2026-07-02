# NIROS Knowledge Pattern Authoring Guide

Engineering specification for every Knowledge Pattern added to `knowledge/patterns/`.

This document is not user-facing documentation. It defines the standard that all pattern authors, reviewers, and tooling must follow before a pattern enters the NIROS Knowledge Base.

---

## Purpose

Every Knowledge Pattern must:

- **Represent one stable psychological construct** — one pattern, one idea. Do not combine unrelated constructs in a single file.
- **Be language-independent internally** — reasoning, linking, and scoring use stable English `canonical_id` values and structured fields, not translated prose.
- **Support multilingual interviews** — `typical_phrases` and `follow_up_questions` must cover supported interview languages.
- **Be machine-readable** — valid YAML that passes `KnowledgePattern` validation via `PatternLoader`.
- **Support adaptive interviewing** — provide follow-up questions and graph relationships that the question suggestion engine can use.
- **Support future hypothesis generation** — evidence fields, confidence rules, and relationships must give the engine traceable material for later inference layers.

Patterns are canonical NIROS constructs. They are not copies of published questionnaires.

---

## Scientific principles

Patterns should be synthesized from modern evidence-based psychology, including:

- Big Five (trait-level context, not questionnaire cloning)
- CBT
- ACT (Acceptance and Commitment Therapy)
- Schema Therapy
- Attachment Theory
- Motivational Interviewing

**Do not copy any single questionnaire.** NIROS does not import PHQ, GAD, IPIP, or other instrument items as pattern content. NIROS creates canonical patterns grounded in evidence, expressed in interview language.

A pattern may reflect concepts familiar from multiple frameworks, but it must be written as one NIROS construct with one `canonical_id`.

---

## Required YAML fields

Each file in `knowledge/patterns/{canonical_id}.yaml` must validate against the `KnowledgePattern` schema in `niros/knowledge.py`.

### `canonical_id`

- **What:** Stable English identifier (`snake_case`).
- **Why:** Primary key for matching, hypotheses, graph edges, and logging.
- **Engine use:** File name, `PatternTag.canonical_id`, relationship targets, loader lookup.

### `name`

- **What:** Human-readable label for authors and reviewers.
- **Why:** Makes patterns identifiable in reviews and debugging.
- **Engine use:** Display and authoring context only; not used for matching.

### `domain`

- **What:** High-level grouping (e.g. `relationships`, `emotion_regulation`, `self_concept`).
- **Why:** Organizes the knowledge base and future routing logic.
- **Engine use:** Filtering, reporting, and future domain-aware interview flow.

### `definition`

- **What:** Short statement of the construct.
- **Why:** Defines what the pattern means inside NIROS.
- **Engine use:** Authoring reference; future explanation and review layers.

### `behavioral_description`

- **What:** Observable tendencies associated with the construct.
- **Why:** Separates outward behavior from abstract definition.
- **Engine use:** Authoring reference; future evidence review and clinician-facing summaries.

### `positive_evidence`

- **What:** List of observations that support the pattern.
- **Why:** Makes evidence expectations explicit and reviewable.
- **Engine use:** Future scoring, contradiction checks, and hypothesis support (not direct diagnosis).

### `negative_evidence`

- **What:** Observations that argue against the pattern.
- **Why:** Prevents one-sided pattern activation.
- **Engine use:** Future confidence reduction and disconfirmation logic.

### `typical_phrases`

- **What:** Map of language code → list of natural-language phrases (`en`, `es`, `ru`).
- **Why:** Enables multilingual substring matching without translation at runtime.
- **Engine use:** `PatternTagger` matches `EvidenceItem.raw_text` against phrases for `EvidenceItem.language`.

### `follow_up_questions`

- **What:** Map of language code → list of open interview questions.
- **Why:** Supplies the next questions when a pattern is matched.
- **Engine use:** `select_follow_up_questions()` and `suggest_next_questions()` for direct pattern questions.

### `related_patterns`

- **What:** List of related `canonical_id` values (informative links).
- **Why:** Documents conceptual neighborhood for authors and future tooling.
- **Engine use:** Authoring and review; not required for runtime matching.

### `relationships`

- **What:** List of semantic edges to other patterns:

```yaml
relationships:
  - target_pattern: people_pleasing
    relation_type: often_leads_to
    weight: 0.82
```

- **Allowed `relation_type` values:**
  - `often_leads_to`
  - `often_coexists_with`
  - `possible_cause`
  - `possible_consequence`
  - `may_strengthen`
  - `may_reduce`
- **`weight`:** Float from `0.0` to `1.0`.
- **Why:** Defines the pattern relationship graph for question routing and future inference.
- **Engine use:** `GraphQuestionSuggester` pulls follow-up questions from related patterns, ranked by `weight`. Missing target YAML is skipped.

### `confidence_rules`

- **What:** Map of rule name → numeric adjustment (e.g. `repeated_evidence: 0.15`, `contradiction_present: -0.25`).
- **Why:** Documents how confidence should move when evidence accumulates or conflicts.
- **Engine use:** Reserved for future hypothesis and pattern confidence engines. Rule names are contractual for later implementation.

### `interview_priority`

- **What:** Integer rank (higher = more important to explore when multiple patterns match).
- **Why:** Breaks ties when the interview cannot pursue every matched pattern immediately.
- **Engine use:** Future adaptive interview scheduling and question ordering beyond graph weights.

### `therapeutic_relevance`

- **What:** Brief statement of why understanding this pattern matters clinically.
- **Why:** Gives human reviewers context for safety and scope.
- **Engine use:** Authoring, review, and future handoff summaries. Must not prescribe treatment.

---

## Writing rules

### Definition

- Concise — one or two sentences.
- Neutral — descriptive, not judgmental.
- Non-diagnostic — never label the person with a disorder or fixed trait claim.

### Behavioral description

- Describe observable behaviors (what the person tends to do or avoid).
- Do not state therapist interpretations as facts (e.g. avoid "this means they have an insecure attachment style" as a certainty).

### Positive evidence

- Concrete observations the interview or transcript might surface.
- Not assumptions about hidden motives unless clearly framed as reported experience.

### Negative evidence

- Credible signs the pattern may not apply.
- Used to prevent overfitting from a single phrase match.

### Typical phrases

- Natural spoken language — how people actually talk in free narrative.
- Not questionnaire items — avoid "Over the last two weeks…" or Likert-style stems.
- Short enough for substring matching; distinctive enough to reduce false positives.
- Provide equivalent meaning across `en`, `es`, and `ru`; do not machine-translate blindly without review.

### Follow-up questions

- Open-ended — invite elaboration.
- Curiosity-driven — explore experience, not confirm a theory.
- Non-leading — do not embed the desired answer.
- Avoid yes/no questions — prefer "What…", "How…", "When…".

### Relationships

- Include only meaningful edges — each relationship must justify its place in the graph.
- Avoid unnecessary graph complexity — do not link every pattern to every other pattern.
- Use `weight` to reflect relative strength of the link, not certainty of diagnosis.
- `target_pattern` must reference a valid `canonical_id`; runtime skips missing targets.

### Confidence rules

- Name rules by intended interpretation (e.g. `repeated_evidence`, `contradiction_present`).
- Use positive values to increase confidence, negative values to decrease.
- Document what each rule means in review notes if the name alone is ambiguous.

### Interview priority

- Higher integer = explore sooner when multiple patterns are active.
- Reserve top priorities (e.g. 8–10) for patterns with strong interview or safety relevance.
- Do not use priority as a substitute for relationship `weight`; they serve different roles.

### Therapeutic relevance

- Explain why understanding the pattern helps interpret the person's experience.
- Do not prescribe treatment, medication, or specific interventions.

---

## Language rules

- **`canonical_id` is always English** — `fear_of_rejection`, not translated slugs.
- **Interview languages currently supported:** `en`, `es`, `ru`.
- **`typical_phrases` and `follow_up_questions` must use these keys** when the pattern is interview-ready.
- **Internal reasoning is language-independent** — matching output uses `canonical_id`; translated text is evidence and presentation only.
- **Icaro/ceremony languages are separate** — do not mix ceremony output languages into pattern interview fields.

---

## Quality checklist

A pattern is accepted only if:

- ✔ Psychologically coherent — one construct, clear definition, consistent evidence.
- ✔ Multilingual — `en`, `es`, and `ru` phrases and follow-ups present and reviewed.
- ✔ Internally consistent — definition, behaviors, evidence, and phrases align.
- ✔ Graph connections valid — `relationships` use allowed `relation_type` values and weights in `0.0–1.0`.
- ✔ Questions are non-leading — follow-ups pass MI-style review.
- ✔ Evidence observable — positive and negative evidence describable from interview content.
- ✔ Loader validates successfully — `PatternLoader().load("{canonical_id}")` passes without error.

Run `pytest tests/test_knowledge_loader.py` after adding or changing a pattern.

---

## Future

Future AI tools may assist drafting definitions, phrases, or follow-up questions. Automated drafts are starting points only.

**Every pattern must satisfy this standard before entering the NIROS Knowledge Base.** Human review remains required for psychological accuracy, safety, multilingual quality, and graph coherence.

No pattern belongs in `knowledge/patterns/` until it validates, tests pass, and the checklist above is complete.
