"""NIROS UI demo pipeline — deterministic mapping for manual UI testing."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from niros.ctpc_tle_adapter import load_psychotherapy_tle_universal_patterns
from niros.knowledge_workspace import DEFAULT_KNOWLEDGE_ROOT
from niros.pattern_person_fit_contracts import PatternFitReport, PatternFitScore, PersonFitProfile
from niros.pattern_person_fit_report import build_pattern_fit_report
from niros.strategy_candidate_builder import StrategyCandidate, build_strategy_candidate
from niros.strategy_explanation import StrategyExplanation, build_strategy_explanation
from niros.voice_transcript import VoiceInput, VoiceTranscript
from niros.whisper_adapter import transcribe_audio_mock
from niros_tle.universal_pattern import SOURCE_TYPE_DEMO, UniversalPattern
from niros_tle.universal_pattern_library import (
    UniversalPatternLibrary,
    build_universal_pattern_library,
    get_pattern_by_id,
)

MODE_TEXT = "Text"
MODE_VOICE_TRANSCRIPT_MOCK = "Voice Transcript Mock"

SHAME_KEYWORDS = (
    "сором",
    "критик",
    "емоцій",
    "shame",
    "critic",
    "emotion",
)

DEFAULT_SHAME_PROFILE = PersonFitProfile(
    profile_id="ui_demo_shame_profile",
    active_signals=(
        "shame_sensitivity",
        "harsh_self_criticism",
        "emotional_avoidance",
    ),
    dominant_domains=("self", "emotion_regulation"),
    risk_signals=("overwhelm_risk",),
    needs=("self_compassion", "emotional_tolerance"),
    session_phase="preparation",
)


@dataclass(frozen=True)
class RuntimePatternLibrarySummary:
    demo_count: int
    ctpc_count: int
    total_count: int

    @property
    def tle_badge_label(self) -> str:
        if self.ctpc_count == 0:
            return "Demo"
        return "Demo + CTPC"


@dataclass(frozen=True)
class NirosDemoResult:
    input_text: str
    profile: PersonFitProfile
    fit_report: PatternFitReport
    strategy: StrategyCandidate
    explanation: StrategyExplanation
    pattern_library: UniversalPatternLibrary
    library_summary: RuntimePatternLibrarySummary
    voice_transcript: VoiceTranscript | None = None


def map_input_text_to_profile(
    text: str,
    *,
    profile_id: str = "ui_demo_profile",
) -> PersonFitProfile:
    """Deterministic demo mapping from pasted text to PersonFitProfile."""
    lowered = text.lower()
    if any(keyword in lowered for keyword in SHAME_KEYWORDS):
        return PersonFitProfile(
            profile_id=profile_id,
            active_signals=DEFAULT_SHAME_PROFILE.active_signals,
            dominant_domains=DEFAULT_SHAME_PROFILE.dominant_domains,
            risk_signals=DEFAULT_SHAME_PROFILE.risk_signals,
            needs=DEFAULT_SHAME_PROFILE.needs,
            session_phase="preparation",
        )
    return PersonFitProfile(
        profile_id=profile_id,
        active_signals=DEFAULT_SHAME_PROFILE.active_signals,
        dominant_domains=DEFAULT_SHAME_PROFILE.dominant_domains,
        risk_signals=DEFAULT_SHAME_PROFILE.risk_signals,
        needs=DEFAULT_SHAME_PROFILE.needs,
        session_phase="preparation",
    )


def _demo_universal_pattern(**kwargs) -> UniversalPattern:
    return UniversalPattern(source_type=SOURCE_TYPE_DEMO, **kwargs)


def demo_pattern_library() -> tuple[UniversalPattern, ...]:
    """Mini universal pattern library for UI demo runs."""
    return (
        _demo_universal_pattern(
            pattern_id="pattern_self_compassion",
            canonical_name="self compassion for shame",
            source_families=("cft",),
            member_pattern_ids=("pattern_self_compassion_member",),
            confidence=0.90,
            target_signals=("shame_sensitivity", "harsh_self_criticism"),
            fit_domains=("self",),
            expected_effects=("self_compassion",),
        ),
        _demo_universal_pattern(
            pattern_id="pattern_acceptance",
            canonical_name="acceptance of difficult emotions",
            source_families=("act",),
            member_pattern_ids=("pattern_acceptance_member",),
            confidence=0.85,
            target_signals=("emotional_avoidance",),
            fit_domains=("emotion_regulation",),
            expected_effects=("emotional_tolerance",),
        ),
        _demo_universal_pattern(
            pattern_id="pattern_stabilization",
            canonical_name="stabilization before deep work",
            source_families=("act",),
            member_pattern_ids=("pattern_stabilization_member",),
            confidence=0.88,
            target_signals=("overwhelm_risk", "emotional_instability"),
            fit_domains=("emotion_regulation",),
            expected_effects=("stabilization",),
        ),
        _demo_universal_pattern(
            pattern_id="pattern_values",
            canonical_name="values clarification",
            source_families=("act",),
            member_pattern_ids=("pattern_values_member",),
            confidence=0.84,
            target_signals=("values_confusion", "low_direction"),
            fit_domains=("values", "meaning"),
            expected_effects=("values_alignment",),
        ),
        _demo_universal_pattern(
            pattern_id="pattern_meaning",
            canonical_name="meaning reconstruction",
            source_families=("act",),
            member_pattern_ids=("pattern_meaning_member",),
            confidence=0.82,
            target_signals=("existential_emptiness", "loss_of_meaning"),
            fit_domains=("meaning",),
            expected_effects=("meaning_making",),
        ),
        _demo_universal_pattern(
            pattern_id="pattern_identity",
            canonical_name="identity reinforcement",
            source_families=("act",),
            member_pattern_ids=("pattern_identity_member",),
            confidence=0.80,
            target_signals=("identity_diffusion", "low_self_coherence"),
            fit_domains=("self", "meaning"),
            expected_effects=("identity_coherence",),
        ),
        _demo_universal_pattern(
            pattern_id="pattern_defusion",
            canonical_name="cognitive defusion",
            source_families=("act",),
            member_pattern_ids=("pattern_defusion_member",),
            confidence=0.86,
            target_signals=("rumination", "catastrophizing"),
            fit_domains=("cognitive",),
            expected_effects=("cognitive_distance",),
        ),
        _demo_universal_pattern(
            pattern_id="pattern_deep_exposure",
            canonical_name="deep emotional exposure",
            source_families=("act",),
            member_pattern_ids=("pattern_deep_exposure_member",),
            confidence=0.90,
            target_signals=("emotional_avoidance",),
            fit_domains=("emotion_regulation",),
            expected_effects=("emotional_tolerance",),
            contraindication_signals=("overwhelm_risk",),
        ),
    )


def merge_runtime_patterns(
    demo_patterns: tuple[UniversalPattern, ...],
    ctpc_patterns: tuple[UniversalPattern, ...],
) -> tuple[UniversalPattern, ...]:
    """Merge demo and CTPC patterns, keeping the first occurrence per pattern_id."""
    merged: list[UniversalPattern] = []
    seen: set[str] = set()
    for pattern in (*demo_patterns, *ctpc_patterns):
        if pattern.pattern_id in seen:
            continue
        merged.append(pattern)
        seen.add(pattern.pattern_id)
    return tuple(merged)


def build_runtime_pattern_library(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> tuple[UniversalPatternLibrary, RuntimePatternLibrarySummary]:
    """Build the active runtime library from demo patterns and psychotherapy_tle CTPC."""
    demo_patterns = demo_pattern_library()
    ctpc_patterns = load_psychotherapy_tle_universal_patterns(workspace_root)
    merged = merge_runtime_patterns(demo_patterns, ctpc_patterns)
    summary = RuntimePatternLibrarySummary(
        demo_count=len(demo_patterns),
        ctpc_count=len(ctpc_patterns),
        total_count=len(merged),
    )
    return build_universal_pattern_library(merged), summary


def get_runtime_pattern_library_summary(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> RuntimePatternLibrarySummary:
    """Return counts for the active runtime pattern library."""
    _, summary = build_runtime_pattern_library(workspace_root)
    return summary


def pattern_source_type_label(source_type: str) -> str:
    """Return a short UI label for one pattern source type."""
    labels = {
        SOURCE_TYPE_DEMO: "Demo",
        "manual_seed": "Manual seed",
        "ctpc": "CTPC",
        "corpus_derived": "Corpus-derived",
        "unspecified": "Unspecified",
    }
    return labels.get(source_type, source_type)


def lookup_pattern_source_type(
    library: UniversalPatternLibrary,
    pattern_id: str,
) -> str:
    """Return the source_type for one pattern in the active library."""
    pattern = get_pattern_by_id(library, pattern_id)
    if pattern is None:
        return "unspecified"
    return pattern.source_type


def run_niros_demo_pipeline(
    text: str,
    *,
    mode: str = MODE_TEXT,
    max_patterns: int = 3,
) -> NirosDemoResult:
    """Run the NIROS demo pipeline from pasted or mock-transcribed text."""
    input_text = text.strip()
    voice_transcript: VoiceTranscript | None = None

    if mode == MODE_VOICE_TRANSCRIPT_MOCK:
        voice_input = VoiceInput(
            audio_path="ui_mock_audio.wav",
            language="uk",
            source="user_upload",
            session_id="ui_voice_session_001",
        )
        voice_transcript = transcribe_audio_mock(voice_input, input_text)

    profile = map_input_text_to_profile(input_text)
    return run_niros_pipeline_from_profile(
        profile,
        input_text=input_text,
        max_patterns=max_patterns,
        voice_transcript=voice_transcript,
    )


def run_niros_pipeline_from_profile(
    profile: PersonFitProfile,
    *,
    input_text: str = "",
    max_patterns: int = 3,
    voice_transcript: VoiceTranscript | None = None,
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> NirosDemoResult:
    """Run Pattern–Person Fit and strategy pipeline from a prepared profile."""
    library, library_summary = build_runtime_pattern_library(workspace_root)
    fit_report = build_pattern_fit_report(profile, library)
    strategy = build_strategy_candidate(fit_report, max_patterns=max_patterns)
    explanation = build_strategy_explanation(strategy)

    return NirosDemoResult(
        input_text=input_text,
        profile=profile,
        fit_report=fit_report,
        strategy=strategy,
        explanation=explanation,
        pattern_library=library,
        library_summary=library_summary,
        voice_transcript=voice_transcript,
    )


def profile_to_snapshot(profile: PersonFitProfile) -> dict:
    """Serialize a PersonFitProfile for session storage."""
    return {
        "profile_id": profile.profile_id,
        "active_signals": list(profile.active_signals),
        "dominant_domains": list(profile.dominant_domains),
        "risk_signals": list(profile.risk_signals),
        "needs": list(profile.needs),
        "session_phase": profile.session_phase,
    }


def _pattern_score_to_dict(score: PatternFitScore) -> dict:
    return asdict(score)


def strategy_to_snapshot(strategy: StrategyCandidate) -> dict:
    """Serialize a StrategyCandidate for session storage."""
    return {
        "strategy_id": strategy.strategy_id,
        "profile_id": strategy.profile_id,
        "strategy_status": strategy.strategy_status,
        "rationale": strategy.rationale,
        "selected_patterns": [_pattern_score_to_dict(s) for s in strategy.selected_patterns],
        "caution_patterns": [_pattern_score_to_dict(s) for s in strategy.caution_patterns],
        "excluded_patterns": [_pattern_score_to_dict(s) for s in strategy.excluded_patterns],
    }


def explanation_to_snapshot(explanation: StrategyExplanation) -> dict:
    """Serialize a StrategyExplanation for session storage."""
    return {
        "strategy_id": explanation.strategy_id,
        "profile_id": explanation.profile_id,
        "summary": explanation.summary,
        "explanation_items": [asdict(item) for item in explanation.explanation_items],
    }


def input_mode_to_repository_value(mode: str) -> str:
    """Map UI mode label to repository input_mode value."""
    if mode == MODE_VOICE_TRANSCRIPT_MOCK:
        return "voice_transcript_mock"
    return "text"
