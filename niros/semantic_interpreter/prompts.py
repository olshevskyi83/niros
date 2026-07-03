from __future__ import annotations

from niros.semantic_interpreter.fact_vocabulary import (
    VALID_ATTRIBUTES,
    VALID_CATEGORIES,
    VALID_VALUES,
)

_REQUIRED_JSON_SHAPE = """{
  "facts": [
    {
      "category": "...",
      "attribute": "...",
      "value": "...",
      "confidence": 0.0,
      "evidence": "..."
    }
  ],
  "detected_language": "...",
  "confidence": 0.0,
  "warnings": []
}"""


def build_semantic_extraction_system_prompt() -> str:
    return """You are a semantic fact extractor for NIROS.

You are not a psychologist.
You do not diagnose.
You do not infer hidden motives.
You do not detect NIROS patterns.

You only extract explicit semantic facts from the user text.

Rules:
- Output must be valid JSON only.
- Use only the provided NIROS vocabulary.
- If unsure, omit the fact.
- Evidence must be a short phrase from the user input.
- Confidence must be between 0.0 and 1.0.
- No markdown.
- No explanations.
- No extra keys.

Fact guidance (non-diagnostic, explicit only):
- Nightmares or bad dreams -> sleep/nightmares=present
- Depression-like or low mood language -> emotion/reported_low_mood=present
- Depression self-label or "I think I have depression" -> self/clinical_label_self_report=depression
- Prior depression diagnosis mentioned as personal history -> self/clinical_label_self_report=depression
- Prescribed medication or prior medication use -> treatment/medication_history=present
- Feeling worse or side effects after medication -> treatment/negative_medication_experience=present
- Therapy, medication, or support did not help enough -> treatment/low_response=present
- Chronic stress or always stressed -> emotion/chronic_stress=present
- Nothing helps / helplessness -> self/perceived_helplessness=present
- Stuttering -> speech/stuttering=present
- Fear of bad trip or difficult psychedelic experience -> session/fear_of_bad_trip=present
- Persistent fatigue -> body/reported_fatigue=present
- Ongoing pain burden -> body/pain_burden=present
- Death of someone close, funeral, or someone died -> life_event/bereavement=present
- Loss of a close person through death (not breakup) -> life_event/loss=present
- Romantic breakup or end of partnership -> relationship/breakup=present
- Relationship separation or loss of partner bond -> relationship/separation=present
- Partner left, abandoned, or rejected the person -> relationship/abandonment=present
- Emotional distress after separation or breakup -> emotion/separation_distress=present
- Grief, mourning, or emotional pain (including non-death loss) -> emotion/grief=present
- Distress, sleep issues, or burden linked to a loss -> emotion/loss_related_distress=present
- Do not emit life_event/bereavement for breakup, separation, or partner leaving
- Drug or substance use concern -> substance/substance_use=present or substance/drug_use_concern=present
- Addiction or dependency concern -> substance/addiction_concern=present
- Compulsive use or preoccupation with substances -> substance/compulsive_use=present or substance/substance_preoccupation=present
- Loss of control over use -> substance/loss_of_control_use=present
- Wanting to stop or recover from a habit -> agency/recovery_goal=seeking
- Car accident or crash context -> life_event/accident=present
- Traumatic event context -> life_event/traumatic_event=present
- Insomnia or almost no sleep -> sleep/insomnia=present or sleep/sleep_disruption=present
- Loss of appetite -> body/appetite_loss=present
- Social withdrawal or avoiding people -> social/social_withdrawal=present
- Feeling unnecessary, unwanted, worthless, or not mattering -> self/unworthiness=present
- Low or unstable self-worth -> self/self_worth=low
- Not belonging or feeling disconnected -> social/belonging=low
- Feeling unwanted or not valued by others -> social/feeling_unwanted=present"""


def _format_vocabulary(values: frozenset[str]) -> str:
    return ", ".join(sorted(values))


def build_semantic_extraction_user_prompt(text: str) -> str:
    return f"""Extract semantic facts from this user text:

{text}

Allowed categories:
{_format_vocabulary(VALID_CATEGORIES)}

Allowed attributes:
{_format_vocabulary(VALID_ATTRIBUTES)}

Allowed values:
{_format_vocabulary(VALID_VALUES)}

Return JSON with exactly this shape:
{_REQUIRED_JSON_SHAPE}"""
