# NIROS Interview Blueprint

Engineering specification for the conversational architecture of NIROS interviews.

This document is not a questionnaire. It is the blueprint used by the Human Understanding Engine (HUE) to design adaptive dialogue, accumulate evidence, refine hypotheses, and produce a structured psychological model.

Implementation may map these phases onto the interview state machine over time. The blueprint defines *what* the conversation should accomplish; the state machine defines *how* the engine transitions at runtime.

---

## Principles

- **Conversation first** — the interview is a dialogue, not a form. The person’s own words are primary data.
- **No fixed questionnaires** — NIROS does not administer rigid item lists. Questions emerge from narrative, matched patterns, and graph-based follow-ups.
- **Adaptive interviewing** — depth, order, and focus shift based on evidence, confidence, and safety signals.
- **Curiosity-driven dialogue** — questions explore experience; they do not prosecute a theory.
- **Multilingual support** — interviews run in `en`, `es`, or `ru`. Internal reasoning uses stable English `canonical_id` values.
- **Evidence accumulation** — each turn adds statements, evidence items, and pattern tags that trace back to source text.
- **Hypothesis refinement** — hypotheses strengthen, weaken, or split as evidence grows; they are never fixed after the first match.

---

## Interview phases

### 1. Consent

**Purpose**  
Establish informed, active consent before any personal exploration. Clarify what NIROS is and is not.

**Main domains**  
Safety, boundaries, data use, right to pause or stop.

**Knowledge Patterns involved**  
None directly. Consent precedes pattern matching.

**Signals to observe**  
Understanding of scope, willingness to proceed, signs of coercion or third-party pressure, urgency level.

**Follow-up strategy**  
Plain-language explanation; confirm consent explicitly; do not begin substantive interview until consent is granted.

**Exit conditions**  
Active consent recorded → proceed to Free Narrative. Lack of consent or coercion → stop interview.

---

### 2. Free Narrative

**Purpose**  
Open the interview without structure. Let the person describe what brought them here in their own way.

**Main domains**  
Declared difficulty, timeline, emotional tone, relationships, functioning, initial risk hints.

**Knowledge Patterns involved**  
Any pattern whose `typical_phrases` match early narrative — e.g. `fear_of_rejection`, `people_pleasing`, `conflict_avoidance`, `fear_of_disappointing_others`.

**Signals to observe**  
Main themes, repeated words, contradictions, intensity, avoidance, help-seeking style, declared vs implied problem.

**Follow-up strategy**  
Minimal interruption; reflective listening; one open clarifier at a time; use matched pattern follow-ups only after sufficient narrative.

**Exit conditions**  
Enough narrative to identify initial domains and pattern candidates, or person naturally completes their opening story → proceed to Life Story or domain indicated by narrative.

---

### 3. Life Story

**Purpose**  
Place current difficulties in personal context — how the person’s path led to the present moment.

**Main domains**  
Development, turning points, losses, achievements, identity shifts, chronic vs acute onset.

**Knowledge Patterns involved**  
Patterns linked to attachment, shame, rejection, and coping — e.g. `fear_of_rejection`, related patterns in the knowledge graph.

**Signals to observe**  
Early relational themes, trauma hints (handle with care), stability vs disruption, narrative coherence, unresolved events.

**Follow-up strategy**  
Timeline questions (“When did that begin to change?”); connect past events to present feelings without interpreting causality as fact.

**Exit conditions**  
Sufficient life-context evidence for downstream domains, or diminishing new information → proceed to Relationships.

---

### 4. Relationships

**Purpose**  
Understand how the person experiences closeness, conflict, trust, distance, and rejection in current relationships.

**Main domains**  
Partnership, friendship, work relationships, social belonging, communication patterns.

**Knowledge Patterns involved**  
`fear_of_rejection`, `people_pleasing`, `conflict_avoidance`, `fear_of_disappointing_others`; graph-suggested follow-ups from `relationships`.

**Signals to observe**  
Fear of disapproval, conflict avoidance, reassurance seeking, boundary difficulty, withdrawal, over-accommodation.

**Follow-up strategy**  
Use direct pattern follow-ups first; then graph-ranked questions from related patterns; explore specific recent interactions.

**Exit conditions**  
Relational evidence stable enough to support or weaken relational hypotheses → proceed to Family.

---

### 5. Family

**Purpose**  
Explore family-of-origin and current family dynamics that shape expectations, roles, and emotional safety.

**Main domains**  
Parental relationships, sibling dynamics, caregiving roles, family conflict, loyalty, estrangement.

**Knowledge Patterns involved**  
Attachment- and rejection-related patterns; `fear_of_rejection`, `people_pleasing`; future family-specific patterns as the knowledge base grows.

**Signals to observe**  
Role rigidity, fear of disappointing family, inherited rules about emotion, unresolved family tension, enmeshment or distance.

**Follow-up strategy**  
Ask for concrete family episodes; avoid forcing causal links; use non-leading questions about “what usually happened” and “what you learned to do.”

**Exit conditions**  
Family domain sufficiently explored or person indicates readiness to move on → proceed to Self.

---

### 6. Self

**Purpose**  
Understand self-concept, inner criticism, standards, identity, and how the person relates to themselves.

**Main domains**  
Self-worth, inner voice, perfectionism, shame, personal standards, agency.

**Knowledge Patterns involved**  
Patterns involving self-evaluation and approval-seeking; graph links to shame and rejection constructs.

**Signals to observe**  
Harsh self-judgment, identity tied to others’ approval, difficulty naming own needs, collapse of self-trust after setbacks.

**Follow-up strategy**  
Contrast “how you see yourself” with “how you act under pressure”; explore exceptions to negative self-beliefs.

**Exit conditions**  
Self-domain evidence supports refinement of active hypotheses → proceed to Emotions.

---

### 7. Emotions

**Purpose**  
Map emotional experience — what is felt, how intensely, how long, and what happens inside when emotions rise.

**Main domains**  
Anxiety, sadness, anger, numbness, guilt, emotional awareness, expression vs suppression.

**Knowledge Patterns involved**  
Emotion-regulation and avoidance patterns; coexisting relational patterns that amplify emotional response.

**Signals to observe**  
Emotional vocabulary, suppression, flooding, guilt after anger, fear of own feelings, alexithymia hints.

**Follow-up strategy**  
Body and moment-focused questions (“What do you notice when that feeling appears?”); avoid labeling emotions for the person.

**Exit conditions**  
Emotional patterns linked to evidence and hypotheses with usable confidence → proceed to Stress & Coping.

---

### 8. Stress & Coping

**Purpose**  
Understand triggers, load, recovery, and what the person does when pressure increases.

**Main domains**  
Stressors, avoidance, rumination, substance use (if disclosed), support seeking, collapse vs overfunctioning.

**Knowledge Patterns involved**  
Avoidance and coping-related patterns — e.g. `conflict_avoidance`; patterns that `may_strengthen` under stress in the graph.

**Signals to observe**  
Maladaptive vs adaptive coping, isolation, compulsive helping, shutdown, escalation under load, loss of boundaries.

**Follow-up strategy**  
Ask what helps even a little; explore recent stress episodes step by step; note contradictions between stated values and under-pressure behavior.

**Exit conditions**  
Coping map sufficient for profile draft and risk review → proceed to Values & Meaning.

---

### 9. Values & Meaning

**Purpose**  
Identify what matters to the person — values, purpose, desired change — independent of symptom labels.

**Main domains**  
Values, meaning, goals, desired life direction, mismatch between values and current behavior (ACT-relevant).

**Knowledge Patterns involved**  
Patterns where behavior contradicts stated values — e.g. people-pleasing vs authenticity; future values-conflict patterns.

**Signals to observe**  
Clear values language, guilt about living inconsistently, loss of meaning, desire for change vs fear of change.

**Follow-up strategy**  
Motivational interviewing style — explore importance and confidence of change without pushing; link values to earlier evidence.

**Exit conditions**  
Values sufficiently articulated to inform profile and handoff → proceed to Closing Reflection.

---

### 10. Closing Reflection

**Purpose**  
Integrate the conversation, confirm understanding, invite corrections, and close safely.

**Main domains**  
Summary check, corrections, emotional landing, next steps (non-prescriptive), consent to retain or delete data if applicable.

**Knowledge Patterns involved**  
All active patterns and hypotheses — presented as working understanding, not diagnosis.

**Signals to observe**  
Agreement or correction from the person, residual distress, new information that reopens a domain, safety status.

**Follow-up strategy**  
Reflect key themes in the person’s language; ask what was missed or wrong; avoid closing while acute risk is unresolved.

**Exit conditions**  
Person acknowledges closure (or requests pause); profile generation may proceed; risk screening complete → handoff.

---

## Global rules

- **Never rush** — depth matters more than phase count. Skipping domains to “finish faster” reduces model quality.
- **Avoid leading questions** — do not suggest the answer inside the question.
- **Prefer open questions** — “What happened?” over “Did you feel anxious?”
- **Revisit hypotheses later** — early pattern matches are provisional. Return to them when new evidence appears.
- **Contradictions are valuable** — inconsistent statements are evidence, not errors. Use `negative_evidence` and confidence rules.
- **Confidence grows gradually** — one phrase match is not confirmation. Repeated, converging evidence raises confidence; contradictions lower it.

Additional constraints:

- No diagnostic labels presented as fact.
- No autonomous medical or treatment instruction.
- Risk signals interrupt normal flow immediately.
- Sensor and voice data (future) are supportive context only — never sole basis for inference.

---

## End goal

NIROS should construct a **progressively refined psychological model** of the person — built from conversation, evidence, pattern tags, relationships, and hypotheses — rather than administer a test and output a score.

The interview produces:

- Traceable evidence linked to source statements
- Pattern activations with multilingual grounding
- Hypotheses with confidence and supporting pattern IDs
- A structured profile that explains *why* NIROS reached its conclusions

The blueprint defines the conversational journey. The engine implements it adaptively — one turn at a time, one evidence item at a time, with curiosity and safety throughout.

---

## Related specifications

- `knowledge/PATTERN_AUTHORING_GUIDE.md` — how to author Knowledge Patterns used during phases
- `niros/knowledge.py` — pattern schema and loader
- `niros/questions.py` — follow-up and graph-based question suggestion
- Vault: `04_Human_Understanding_Engine/` — HUE overview and state machine
