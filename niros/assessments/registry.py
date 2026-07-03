from __future__ import annotations

from collections.abc import Callable

from niros.assessment import AssessmentItem, AssessmentResponse, AssessmentResult
from niros.assessments.cognitive_patterns_domain_short import (
    get_cognitive_patterns_domain_short_items,
    score_cognitive_patterns_domain_short,
)
from niros.assessments.emotion_regulation_domain_short import (
    get_emotion_regulation_domain_short_items,
    score_emotion_regulation_domain_short,
)
from niros.assessments.emotional_flexibility_domain_short import (
    get_emotional_flexibility_domain_short_items,
    score_emotional_flexibility_domain_short,
)
from niros.assessments.relationships_domain_short import (
    get_relationships_domain_short_items,
    score_relationships_domain_short,
)
from niros.assessments.self_domain_short import get_self_domain_short_items, score_self_domain_short
from niros.assessments.values_identity_domain_short import (
    get_values_identity_domain_short_items,
    score_values_identity_domain_short,
)
from niros.assessments.anxiety_short import get_anxiety_short_items, score_anxiety_short
from niros.assessments.behavioral_addiction_short import (
    get_behavioral_addiction_short_items,
    score_behavioral_addiction_short,
)
from niros.assessments.big_five_short import get_big_five_short_items, score_big_five_short
from niros.assessments.grief_loss_short import get_grief_loss_short_items, score_grief_loss_short
from niros.assessments.low_mood_short import get_low_mood_short_items, score_low_mood_short
from niros.assessments.meaning_purpose_short import (
    get_meaning_purpose_short_items,
    score_meaning_purpose_short,
)
from niros.assessments.pain_fatigue_short import get_pain_fatigue_short_items, score_pain_fatigue_short
from niros.assessments.psychedelic_concern_short import (
    get_psychedelic_concern_short_items,
    score_psychedelic_concern_short,
)
from niros.assessments.sleep_short import get_sleep_short_items, score_sleep_short
from niros.assessments.speech_anxiety_short import (
    get_speech_anxiety_short_items,
    score_speech_anxiety_short,
)
from niros.assessments.substance_use_short import get_substance_use_short_items, score_substance_use_short
from niros.assessments.trauma_stress_short import get_trauma_stress_short_items, score_trauma_stress_short

GetItemsFn = Callable[[str], list[AssessmentItem]]
ScoreModuleFn = Callable[[list[AssessmentResponse]], list[AssessmentResult]]

MODULE_REGISTRY: dict[str, tuple[GetItemsFn, ScoreModuleFn]] = {
    "big-five-short": (get_big_five_short_items, score_big_five_short),
    "low-mood-short": (get_low_mood_short_items, score_low_mood_short),
    "anxiety-short": (get_anxiety_short_items, score_anxiety_short),
    "sleep-short": (get_sleep_short_items, score_sleep_short),
    "trauma-stress-short": (get_trauma_stress_short_items, score_trauma_stress_short),
    "grief-loss-short": (get_grief_loss_short_items, score_grief_loss_short),
    "substance-use-short": (get_substance_use_short_items, score_substance_use_short),
    "behavioral-addiction-short": (
        get_behavioral_addiction_short_items,
        score_behavioral_addiction_short,
    ),
    "pain-fatigue-short": (get_pain_fatigue_short_items, score_pain_fatigue_short),
    "speech-anxiety-short": (get_speech_anxiety_short_items, score_speech_anxiety_short),
    "psychedelic-concern-short": (
        get_psychedelic_concern_short_items,
        score_psychedelic_concern_short,
    ),
    "meaning-purpose-short": (get_meaning_purpose_short_items, score_meaning_purpose_short),
    "self-domain-short": (get_self_domain_short_items, score_self_domain_short),
    "emotion-regulation-domain-short": (
        get_emotion_regulation_domain_short_items,
        score_emotion_regulation_domain_short,
    ),
    "cognitive-patterns-domain-short": (
        get_cognitive_patterns_domain_short_items,
        score_cognitive_patterns_domain_short,
    ),
    "relationships-domain-short": (
        get_relationships_domain_short_items,
        score_relationships_domain_short,
    ),
    "values-identity-domain-short": (
        get_values_identity_domain_short_items,
        score_values_identity_domain_short,
    ),
    "emotional-flexibility-domain-short": (
        get_emotional_flexibility_domain_short_items,
        score_emotional_flexibility_domain_short,
    ),
}


def list_available_modules() -> list[str]:
    return sorted(MODULE_REGISTRY)


def get_assessment_module_items(module_id: str, language: str = "en") -> list[AssessmentItem]:
    try:
        get_items, _ = MODULE_REGISTRY[module_id]
    except KeyError as exc:
        raise ValueError(f"Unknown assessment module: {module_id}") from exc
    return get_items(language)


def score_assessment_module(
    module_id: str,
    responses: list[AssessmentResponse],
) -> list[AssessmentResult]:
    try:
        _, score_module = MODULE_REGISTRY[module_id]
    except KeyError as exc:
        raise ValueError(f"Unknown assessment module: {module_id}") from exc
    return score_module(responses)
