# Evidence Levels

NIROS must clearly separate evidence quality.

| Level | Meaning | Use in NIROS |
|---|---|---|
| E1 | Meta-analysis / strong systematic review | Can support design principles |
| E2 | RCT / controlled clinical study | Can support protocol design |
| E3 | Observational / cohort / validated clinical practice | Can support risk and assessment logic |
| E4 | Mechanistic neuroscience / psychophysiology | Can support hypotheses, not outcomes alone |
| E5 | Expert opinion / clinical reasoning | Useful, but must be labeled |
| E6 | Product hypothesis | Must be tested before claiming value |

## Evidence tagging template

```yaml
evidence_level: E1-E6
claim_type: established | plausible | speculative | design_hypothesis
source_status: unread | skimmed | reviewed | validated
reviewer: human | AI-assisted | clinician
```

## Rule

A design can be inspired by weak evidence, but a claim to users must not sound stronger than the evidence.
