from niros.human_digital_fingerprint import (
    NO_EVIDENCE_PROFILE_TEXT,
    build_human_digital_fingerprint,
)
from niros.human_profile_summary import build_human_profile_summary
from niros.intervention_strategy import (
    EMPTY_PROFILE_STRATEGY,
    InterventionStrategy,
    build_intervention_strategy,
    is_high_grounding,
    render_intervention_strategy,
)
from niros.models import SupportedLanguage
from niros.patterns import PatternTag


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str,
    sequence: int,
    confidence: float = 1.0,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-strategy-001",
        evidence_id=f"session-strategy-001:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def _fingerprint_from_patterns(pattern_ids: list[str]) -> dict:
    tags = [
        _pattern_tag(pattern_id, tag_id=f"tag-{index}", sequence=index)
        for index, pattern_id in enumerate(pattern_ids)
    ]
    return build_human_digital_fingerprint(detected_patterns=tags)


def test_empty_profile_produces_safe_grounding_first_strategy():
    fingerprint = build_human_digital_fingerprint(detected_patterns=[])

    strategy = build_intervention_strategy(fingerprint)

    assert strategy == EMPTY_PROFILE_STRATEGY
    assert strategy.pacing == "slow"
    assert strategy.emotional_intensity == "low"
    assert is_high_grounding(strategy.grounding_priority)
    assert strategy.exploration_priority == "low"
    assert strategy.cognitive_load == "low"


def test_existential_fear_increases_grounding_and_lowers_cognitive_load():
    strategy = build_intervention_strategy(_fingerprint_from_patterns(["existential_fear"]))

    assert strategy.pacing == "slow"
    assert is_high_grounding(strategy.grounding_priority)
    assert strategy.cognitive_load == "low"
    assert strategy.directness == "low"
    assert strategy.metaphor_level == "medium"
    assert strategy.emotional_intensity == "low_to_medium"


def test_fibromyalgia_increases_body_focus_and_shorter_duration():
    strategy = build_intervention_strategy(_fingerprint_from_patterns(["fibromyalgia_signal"]))

    assert strategy.body_focus == "high"
    assert strategy.pacing == "slow"
    assert strategy.emotional_intensity == "low"
    assert strategy.cognitive_load == "low"
    assert strategy.suggested_duration == 40


def test_chronic_pain_increases_body_focus_and_shorter_duration():
    strategy = build_intervention_strategy(_fingerprint_from_patterns(["chronic_pain_burden"]))

    assert strategy.body_focus == "high"
    assert strategy.suggested_duration == 40


def test_speech_anxiety_lowers_directness_and_increases_repetition():
    strategy = build_intervention_strategy(_fingerprint_from_patterns(["speech_anxiety"]))

    assert strategy.directness == "low"
    assert strategy.repetition_level == "high"
    assert strategy.emotional_intensity == "low"
    assert strategy.self_focus == "medium"


def test_psychedelic_anxiety_increases_grounding_and_reduces_exploration():
    strategy = build_intervention_strategy(_fingerprint_from_patterns(["psychedelic_anxiety"]))

    assert strategy.grounding_priority == "very_high"
    assert strategy.exploration_priority == "low_to_medium"
    assert strategy.directness == "low"
    assert strategy.metaphor_level == "low_to_medium"


def test_meaning_seeking_increases_spirituality_metaphor_and_integration():
    strategy = build_intervention_strategy(_fingerprint_from_patterns(["meaning_seeking"]))

    assert strategy.spirituality_focus == "medium_to_high"
    assert strategy.metaphor_level == "medium_to_high"
    assert strategy.integration_priority == "high"


def test_build_intervention_strategy_is_deterministic():
    fingerprint = _fingerprint_from_patterns(["existential_fear", "emotional_distress_signal"])

    assert build_intervention_strategy(fingerprint) == build_intervention_strategy(fingerprint)


def test_build_intervention_strategy_accepts_human_profile_summary():
    profile = build_human_profile_summary(
        [
            _pattern_tag("speech_anxiety", tag_id="tag-1", sequence=0),
            _pattern_tag("stuttering_signal", tag_id="tag-2", sequence=1),
        ]
    )
    fingerprint = _fingerprint_from_patterns(["speech_anxiety", "stuttering_signal"])

    assert build_intervention_strategy(profile) == build_intervention_strategy(fingerprint)


def test_strategy_exposes_all_required_fields():
    strategy = build_intervention_strategy(_fingerprint_from_patterns(["rumination"]))
    payload = strategy.to_dict()

    assert isinstance(strategy, InterventionStrategy)
    assert "strategy_notes" in payload
    assert isinstance(payload["suggested_duration"], int)


def test_render_intervention_strategy_includes_all_sections():
    strategy = build_intervention_strategy(_fingerprint_from_patterns(["existential_fear"]))
    rendered = render_intervention_strategy(strategy)

    assert rendered.startswith("=== NIROS Intervention Strategy ===")
    for label in (
        "Pacing:",
        "Emotional intensity:",
        "Metaphor level:",
        "Directness:",
        "Repetition:",
        "Grounding priority:",
        "Exploration priority:",
        "Integration priority:",
        "Body focus:",
        "Relationship focus:",
        "Self focus:",
        "Spirituality focus:",
        "Cognitive load:",
        "Suggested duration:",
        "Notes:",
    ):
        assert label in rendered


def test_fingerprint_summary_is_not_generic_when_patterns_present():
    fingerprint = _fingerprint_from_patterns(["existential_fear"])

    assert fingerprint["summary_text"] != NO_EVIDENCE_PROFILE_TEXT
    assert fingerprint["patterns"]["primary_pattern"] is not None
