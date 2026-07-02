# Risk Assessment

Risk assessment is mandatory before any therapeutic recommendation.

## Risk categories

- Acute self-harm or suicidal intent
- Psychosis or mania indicators
- Severe dissociation / destabilization
- Substance dependence or intoxication
- Medical instability
- Unsafe environment
- Coercion or lack of consent

## Risk flow

```mermaid
flowchart TD
    A[Assessment input] --> B{Risk signal?}
    B -->|No| C[Continue]
    B -->|Possible| D[Ask structured safety questions]
    D --> E{Acute risk?}
    E -->|Yes| F[Escalation / emergency / human support]
    E -->|No| G[Flag + continue with caution]
```

## Cursor implementation note

Risk checks should run before generating deep follow-up questions.
