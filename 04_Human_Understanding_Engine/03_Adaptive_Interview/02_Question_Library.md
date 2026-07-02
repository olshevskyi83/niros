# Question Library

The question library keeps NIROS predictable and safe.

## Question object

```yaml
question_id:
domain:
intent:
text:
allowed_followups:
risk_sensitive: true | false
contraindications:
updates_fields:
```

## Example domains

- mood
- anxiety
- sleep
- trauma
- relationships
- grief
- burnout
- substance_use
- safety
- values
- readiness

## Example

```yaml
question_id: anxiety_impact_001
domain: anxiety
intent: assess_functional_impact
text: Has anxiety recently stopped you from doing something important or normal for you?
allowed_followups:
  - anxiety_timeline_001
  - anxiety_body_001
updates_fields:
  - anxiety.functional_impact
```

## Cursor rule

Do not scatter questions across random files. Keep reusable questions in structured libraries.
