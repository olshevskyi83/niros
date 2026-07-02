---
name: big-five-assessment
description: >-
  Big Five (OCEAN) personality assessment domain knowledge for NIROS — domains,
  facets, question design, reverse scoring, reliability, adaptive questioning,
  JSON output, scoring, and confidence estimation. Use when designing,
  implementing, reviewing, or scoring Big Five questionnaires in the Human
  Understanding Engine. Domain knowledge only; does not implement code.
---

# Big Five Assessment

Reusable psychological domain knowledge for implementing a Big Five questionnaire inside NIROS.

## NIROS constraints

- Big Five scores are **descriptive trait estimates**, not diagnoses or clinical labels.
- Prefer **scale-inspired** NIROS items unless a fully licensed validated instrument (e.g. NEO-PI-R) is explicitly approved and implemented.
- Every score must be **explainable**: cite contributing items and response patterns.
- Integrate with HUE adaptive interview — Big Five is one structured signal among others, not the whole assessment.
- User-facing copy: plain language, non-judgmental, no personality disorder framing.

---

## The five domains (OCEAN)

| Code | Domain | High pole (brief) | Low pole (brief) |
|------|--------|-------------------|------------------|
| **O** | Openness | Curious, imaginative, open to experience | Practical, conventional, prefers familiar |
| **C** | Conscientiousness | Organized, disciplined, goal-directed | Flexible, spontaneous, less structured |
| **E** | Extraversion | Sociable, energetic, assertive | Reserved, quiet, low social stimulation need |
| **A** | Agreeableness | Cooperative, trusting, compassionate | Competitive, skeptical, direct |
| **N** | Neuroticism | Emotionally reactive, stress-sensitive | Emotionally stable, calm under stress |

**Neuroticism** is often labeled **Emotional Stability** when reverse-scored for presentation. In NIROS internal JSON, keep the key `neuroticism` for consistency with research literature; user-facing summaries may describe "higher stability" when score is low on N.

### Facets

Each domain has **6 facets** (Costa & McCrae NEO-PI-R model). Facets allow finer-grained adaptive probing and explainable output.

See [facets.md](facets.md) for the full facet list, definitions, and example item stems.

---

## Question design principles

### Format

- **Likert scale (default):** 5-point — `1 = strongly disagree` … `5 = strongly agree`.
- **One construct per item.** No double-barreled questions ("I am organized and punctual" → split).
- **Behavioral and concrete** beats abstract trait labels ("I follow a daily plan" vs "I am conscientious").
- **Simple reading level.** Short sentences; avoid jargon and clinical terms.

### Keying balance

- Mix ** positively keyed** (high score = high trait) and **reverse-keyed** items within each domain/facet.
- Aim for ~40–50% reverse-keyed per domain to reduce acquiescence bias.
- Never use double negatives ("I do not rarely feel…").

### Domain coverage

- Minimum **2 items per facet** in a full form; **1–2 items per domain** in a short screen.
- Items should sample facets evenly within a domain when not using adaptive mode.

### NIROS tone

- Present tense, first person: "I …"
- Non-judgmental: avoid moralizing (especially for A and C).
- Culturally cautious: items about social behavior (E, A) may misfire across cultures — flag low confidence when applicable.
- Do not reference disorders, pathology, or fixed identity ("I am an anxious person").

### Item metadata (required per question)

Each item must carry:

| Field | Purpose |
|-------|---------|
| `item_id` | Stable identifier (e.g. `bf_o_fantasy_01`) |
| `domain` | `O`, `C`, `E`, `A`, or `N` |
| `facet` | Facet code (e.g. `O1`) |
| `keyed` | `positive` or `reverse` |
| `text` | User-facing question |
| `scale_min` / `scale_max` | Usually 1 and 5 |

---

## Reverse scoring

Reverse-keyed items measure the **low pole** of the trait. Recode before aggregation.

**5-point scale recode:**

| Raw response | Recoded score |
|--------------|---------------|
| 1 | 5 |
| 2 | 4 |
| 3 | 3 |
| 4 | 2 |
| 5 | 1 |

**General formula:** `recoded = (scale_min + scale_max) - raw`

Apply recoding **per item** based on `keyed`, then aggregate. Never reverse-score at the domain level.

**Quality checks:**

- Flag items where recoded value correlates unexpectedly with sibling items (possible mis-keying or ambiguous wording).
- Treat `3` (neutral) as low information — see confidence section.

---

## Reliability

### Internal consistency

- **Domain level:** Cronbach's α ≥ 0.70 is acceptable for short forms; ≥ 0.80 for full domains.
- **Facet level:** α ≥ 0.60 acceptable with 2–4 items; unstable below 2 items.
- **NIROS short/adaptive forms** will often run below traditional thresholds — compensate with **confidence scores** and avoid over-interpreting single-item facets.

### Factors that lower reliability in NIROS

- Too few items per domain/facet
- Adaptive termination before minimum items met
- Acquiescence (all 4s and 5s) or extreme negative responding (all 1s and 2s)
- Rapid inconsistent answers (high variance on similar items)
- Social desirability / faking good on C and A

### Response quality flags

Emit quality flags (not diagnoses) when detected:

| Flag | Detection heuristic |
|------|---------------------|
| `acquiescence_bias` | >80% responses ≥ 4 |
| `negative_extreme` | >80% responses ≤ 2 |
| `inconsistent_pair` | Divergence ≥ 3 points on parallel positive/reverse pair |
| `neutral_streak` | ≥ 60% responses exactly 3 |
| `insufficient_items` | Domain answered with fewer than minimum items |

---

## Adaptive questioning

Big Five in NIROS should follow HUE adaptive logic: ask enough to estimate traits with stated confidence, no fixed 240-item battery.

### Phases

1. **Domain screen (breadth):** 1–2 items per domain (10 items max) — mixed facets, balanced keying.
2. **Facet probe (depth):** If domain confidence < threshold OR hypothesis engine needs clarity on a trait-relevant theme, ask 1–2 items targeting the weakest facet(s).
3. **Consistency check:** Optional paired item if `inconsistent_pair` flag or confidence still low.
4. **Stop rules:** Stop when all domain confidences ≥ threshold OR max item budget reached.

### Selection rules

| Condition | Next action |
|-----------|-------------|
| Domain confidence ≥ 0.75 | Stop probing that domain |
| Domain confidence 0.50–0.74 | Add 1 item from lowest-coverage facet |
| Domain confidence < 0.50 | Add 2 items from lowest-coverage facets |
| Quality flag raised | Add consistency-check item or note low confidence |
| User fatigue / max turns | Stop; report with reduced confidence |

### Minimum items before reporting

| Level | Minimum items |
|-------|---------------|
| Domain score | 2 (3+ preferred) |
| Facet score | 1 (2+ preferred) |
| Full profile summary | At least 1 item in ≥ 4 of 5 domains |

### Link to HUE

- Big Five module runs in `domain_screening` or dedicated personality block — not during acute `risk_screening`.
- Trait scores feed **hypotheses** (e.g. high N + sleep items → stress-vulnerability theme) — they do not override declared problem.
- Pass item-level evidence to profile `hypotheses[].evidence_for`.

---

## Scoring algorithm

All scoring uses **recoded item values** on the 1–5 scale unless normalized.

### Step 1 — Item recode

For each answered item: apply reverse scoring if `keyed == reverse`.

### Step 2 — Facet score

```
facet_score = mean(recoded_items for facet)
```

If only one item: `facet_score = that item value`. Mark facet confidence lower.

### Step 3 — Domain score

```
domain_score = mean(facet_scores with ≥1 item)
```

Alternative (item-level, common in short forms):

```
domain_score = mean(all recoded items in domain)
```

Use one method consistently per implementation. Facet-first weighting is preferred when facet data exists.

### Step 4 — Normalization (optional)

For NIROS JSON, store both raw mean and normalized:

```
domain_normalized = (domain_score - 1) / 4   # maps 1–5 → 0.0–1.0
```

**Labels (user-facing, non-diagnostic):**

| Normalized range | Descriptor |
|------------------|------------|
| 0.00 – 0.24 | lower range |
| 0.25 – 0.44 | somewhat lower |
| 0.45 – 0.55 | moderate |
| 0.56 – 0.74 | somewhat higher |
| 0.75 – 1.00 | higher range |

Never use clinical or fixed typology labels ("neurotic", "disordered", "pathological").

### Step 5 — Evidence attachment

For each domain, attach:

- `items_used`: list of `item_id` + recoded value
- `facet_breakdown`: facet code → score
- `quality_flags`: any detected flags

---

## Confidence estimation

Confidence is **epistemic** — how much item evidence supports the score — not trait certainty in the person.

### Per-domain confidence

Start at `0.0`. Add components (cap at `1.0`):

| Component | Weight | Rule |
|-----------|--------|------|
| Item count | up to 0.40 | `min(n_items / 6, 1.0) × 0.40` |
| Response variance | up to 0.25 | Lower variance among same-keyed items → higher; all identical → reduce by 0.10 |
| Facet coverage | up to 0.20 | `facets_with_items / 6 × 0.20` |
| Consistency | up to 0.15 | No `inconsistent_pair` flag → +0.15; flag present → +0.05 |

Subtract penalties:

| Penalty | Amount |
|---------|--------|
| `insufficient_items` | −0.30 |
| `acquiescence_bias` or `negative_extreme` | −0.15 |
| `neutral_streak` | −0.10 |
| Only 1 item in domain | −0.20 |

Floor at `0.10`, ceiling at `0.95`. Never report `1.0` — personality estimates are always provisional.

### Per-facet confidence

```
facet_confidence = min(0.95, 0.35 + 0.30 × n_items + 0.30 if no inconsistency)
```

Single-item facet: cap at `0.55`.

### Overall assessment confidence

```
overall = mean(domain_confidences) × (domains_with_data / 5)
```

Report `overall` with profile; suppress domain interpretations when domain confidence < 0.50.

---

## JSON output structure

Designed for NIROS HUE integration. Validate against project schemas when wiring to `HumanProfile`.

```json
{
  "assessment_id": "bf5_<session_id>",
  "instrument": "niros-big-five-adaptive-v1",
  "completed_at": "<ISO-8601>",
  "items_answered": 12,
  "item_budget_max": 20,
  "response_quality_flags": [],
  "domains": {
    "openness": {
      "score_raw": 3.6,
      "score_normalized": 0.65,
      "descriptor": "somewhat higher",
      "confidence": 0.72,
      "facets": {
        "O1": { "score_raw": 3.5, "confidence": 0.55, "items_used": ["bf_o_fantasy_01"] },
        "O2": { "score_raw": 3.8, "confidence": 0.58, "items_used": ["bf_o_aesthetics_01"] }
      },
      "items_used": [
        { "item_id": "bf_o_fantasy_01", "raw": 4, "recoded": 4, "keyed": "positive" }
      ]
    },
    "conscientiousness": { },
    "extraversion": { },
    "agreeableness": { },
    "neuroticism": { }
  },
  "overall_confidence": 0.68,
  "interpretation_notes": "Trait estimates from self-report; not diagnostic. Low facet coverage on Openness facets O3–O6.",
  "adaptive_trace": [
    { "turn": 1, "action": "domain_screen", "item_id": "bf_o_fantasy_01" },
    { "turn": 8, "action": "facet_probe", "domain": "N", "facet": "N1", "reason": "confidence_below_threshold" }
  ]
}
```

### Required top-level fields

`assessment_id`, `instrument`, `items_answered`, `domains` (all five keys present — use `null` scores with `confidence: 0` if unanswered), `overall_confidence`, `interpretation_notes`.

### Handoff to HumanProfile

Map into profile extensions or hypotheses:

- Domain descriptors → supporting evidence for temperament/regulation hypotheses
- High **N** + high confidence → evidence for stress-reactivity themes (not "anxiety disorder")
- High **C** → evidence for structure/discipline preferences in session planning
- Always include confidence and `interpretation_notes` in handoff metadata

---

## Implementation checklist (for agents)

When applying this skill to NIROS work:

- [ ] Items have stable IDs, domain, facet, keying metadata
- [ ] Reverse scoring applied before aggregation
- [ ] Minimum item thresholds enforced before reporting
- [ ] Confidence computed per domain and overall
- [ ] Quality flags surfaced, not hidden
- [ ] JSON includes evidence (`items_used`, `adaptive_trace`)
- [ ] User-facing copy reviewed by `niros-psychologist`; no diagnostic language
- [ ] Adaptive stop rules respect HUE turn budget and safety gates

---

## Additional resources

- Full facet definitions and example item stems: [facets.md](facets.md)
