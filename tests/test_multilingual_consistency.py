"""Multilingual consistency — stable Human Digital Fingerprint across languages.

Each synthetic case is expressed in English, Ukrainian, German, and Spanish using
pattern-library phrases where available. German narratives reuse English pattern
anchors because the knowledge base does not yet define ``de`` typical phrases;
intake and framing remain German. The goal is stable psychological understanding,
not identical wording.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from demo_interview import run_interview_session
from niros.adaptive_assessment_selector import ALL_ASSESSMENT_MODULE_IDS, select_assessment_modules
from niros.assessment_runner import ASSESSMENT_ADAPTIVE, neutral_answers_for_module
from niros.human_profile_report import (
    build_human_profile_report_from_tags,
    render_human_profile_report,
)
from niros.human_profile_summary import build_human_profile_summary
from niros.intervention_strategy import (
    STRATEGY_CONFIDENCE_RANK,
    build_intervention_strategy,
    render_intervention_strategy,
)
from niros.scenario_blueprint import build_scenario_blueprint, render_scenario_blueprint
from niros.session_simulation import simulate_session
from niros.session_timeline_renderer import render_session_timeline
from run_niros import build_coverage_from_session, build_fingerprint_from_session

LANGUAGES: tuple[str, ...] = ("en", "uk", "es", "de")
REFERENCE_LANGUAGE = "en"

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(is|e|ed|ing)?|disorder|patholog|clinical syndrome|bipolar|"
    r"ptsd|narcissistic personality|borderline personality)\b",
    re.IGNORECASE,
)

_INTAKE_TAIL: dict[str, dict[str, str]] = {
    "en": {
        "duration": "several months",
        "perceived_causes": "ongoing stress and inner struggle",
        "current_impact": "daily emotional burden",
        "previous_attempts": "talking with friends",
        "desired_outcome": "understand myself and feel more stable",
    },
    "uk": {
        "duration": "кілька місяців",
        "perceived_causes": "постійний стрес і внутрішня боротьба",
        "current_impact": "щоденне емоційне навантаження",
        "previous_attempts": "розмови з друзями",
        "desired_outcome": "краще зрозуміти себе і почуватися стабільніше",
    },
    "es": {
        "duration": "varios meses",
        "perceived_causes": "estrés continuo y lucha interior",
        "current_impact": "carga emocional diaria",
        "previous_attempts": "hablar con amigos",
        "desired_outcome": "entenderme mejor y sentirme más estable",
    },
    "de": {
        "duration": "seit Monaten",
        "perceived_causes": "anhaltender Stress und innerer Kampf",
        "current_impact": "tägliche emotionale Belastung",
        "previous_attempts": "Gespräche mit Freunden",
        "desired_outcome": "mich besser verstehen und stabiler fühlen",
    },
}


@dataclass(frozen=True)
class MultilingualCase:
    case_id: str
    domain_label: str
    pattern_families: tuple[frozenset[str], ...]
    primary_domain_fragments: tuple[str, ...]
    assessment_fragments: tuple[str, ...]
    primary_strategy_focus: str
    presenting_problem: dict[str, str]
    narratives: dict[str, str]


MULTILINGUAL_CASES: tuple[MultilingualCase, ...] = (
    MultilingualCase(
        case_id="consistency_self",
        domain_label="Self",
        pattern_families=(
            frozenset({"unworthiness_signal", "harsh_self_criticism", "self_worth_instability"}),
        ),
        primary_domain_fragments=("self_domain",),
        assessment_fragments=("self-domain",),
        primary_strategy_focus="self-worth / self-criticism",
        presenting_problem={
            "en": "I constantly criticize myself and feel not good enough.",
            "uk": "Я постійно себе критикую і відчуваю, що недостатньо хороший.",
            "es": "Me critico constantemente y siento que no soy suficiente.",
            "de": "Ich kritisiere mich ständig und fühle mich nicht gut genug.",
        },
        narratives={
            "en": (
                "deep down I feel I'm not enough. My inner voice is very critical. "
                "I cannot stop criticizing myself after I mess up."
            ),
            "uk": (
                "не відчуваю себе гідним хороших речей. "
                "коли мене критикують, швидко почуваюся невартим. "
                "я не впевнений, чи я достатньо хороший як людина."
            ),
            "es": (
                "no me siento digno de cosas buenas. Mi voz interior es muy crítica. "
                "Me castigo por pequeños errores."
            ),
            "de": (
                "deep down I feel I'm not enough. My inner voice is very critical. "
                "I cannot stop criticizing myself after I mess up."
            ),
        },
    ),
    MultilingualCase(
        case_id="consistency_shame",
        domain_label="Shame",
        pattern_families=(
            frozenset({"shame_sensitivity", "shame_after_vulnerability"}),
        ),
        primary_domain_fragments=("self_domain",),
        assessment_fragments=("self-domain",),
        primary_strategy_focus="self-worth / self-criticism",
        presenting_problem={
            "en": "I feel ashamed of who I am.",
            "uk": "Мені соромно за те, ким я є.",
            "es": "Me da vergüenza quien soy.",
            "de": "Ich schäme mich für das, wer ich bin.",
        },
        narratives={
            "en": (
                "I often feel embarrassed even when no one is watching. "
                "When I make a mistake, I feel like a failure."
            ),
            "uk": (
                "мені соромно після того, як відкрився. "
                "часто відчуваю сором, коли показую вразливість."
            ),
            "es": (
                "A menudo me siento avergonzado incluso cuando nadie me mira. "
                "Cuando cometo un error, siento que soy un fracaso."
            ),
            "de": (
                "I often feel embarrassed even when no one is watching. "
                "When I make a mistake, I feel like a failure."
            ),
        },
    ),
    MultilingualCase(
        case_id="consistency_low_mood",
        domain_label="Low Mood",
        pattern_families=(
            frozenset({"anhedonia_signal", "depressed_mood_signal", "low_mood_signal"}),
        ),
        primary_domain_fragments=("low_mood",),
        assessment_fragments=("low-mood",),
        primary_strategy_focus="presenting context",
        presenting_problem={
            "en": "I no longer enjoy things and every day feels heavy.",
            "uk": "Я більше не отримую задоволення, кожен день важкий.",
            "es": "Ya no disfruto las cosas y cada día se siente pesado.",
            "de": "Ich genieße Dinge nicht mehr und jeder Tag fühlt sich schwer an.",
        },
        narratives={
            "en": (
                "I feel down most of the time. nothing really brings me joy anymore. "
                "I don't enjoy things I used to love."
            ),
            "uk": (
                "більшість часу почуваюся пригнічено. нічого вже не приносить мені радості. "
                "не отримую задоволення від того, що раніше любив."
            ),
            "es": (
                "me siento decaído la mayor parte del tiempo. nada me trae alegría como antes. "
                "ya no disfruto las cosas que solía amar."
            ),
            "de": (
                "I feel down most of the time. nothing really brings me joy anymore. "
                "I don't enjoy things I used to love."
            ),
        },
    ),
    MultilingualCase(
        case_id="consistency_grief",
        domain_label="Grief / Loss",
        pattern_families=(
            frozenset({"grief_signal", "bereavement_context", "loss_related_distress"}),
        ),
        primary_domain_fragments=("grief",),
        assessment_fragments=("grief-loss",),
        primary_strategy_focus="meaning / purpose",
        presenting_problem={
            "en": "I lost someone important and never recovered emotionally.",
            "uk": "Я втратив близьку людину і не можу відновитися.",
            "es": "Perdí a alguien importante y no me recuperé emocionalmente.",
            "de": "Ich habe jemanden Wichtiges verloren und mich nie erholt.",
        },
        narratives={
            "en": (
                "I lost someone close to me and I am grieving. "
                "the grief feels overwhelming. I cannot get over the loss."
            ),
            "uk": (
                "я втратив близьку людину. я переживаю втрату. "
                "горе не відпускає. я не можу пережити втрату."
            ),
            "es": (
                "estoy de luto. el duelo me agota. me cuesta procesar la pérdida."
            ),
            "de": (
                "I lost someone close to me and I am grieving. "
                "the grief feels overwhelming. I cannot get over the loss."
            ),
        },
    ),
    MultilingualCase(
        case_id="consistency_meaning",
        domain_label="Meaning / Purpose",
        pattern_families=(frozenset({"loss_of_meaning", "hopelessness_signal", "meaning_seeking"}),),
        primary_domain_fragments=("meaning",),
        assessment_fragments=("meaning-purpose", "grief-loss"),
        primary_strategy_focus="meaning / purpose",
        presenting_problem={
            "en": "Everything feels meaningless.",
            "uk": "Усе здається безглуздим.",
            "es": "Todo se siente sin sentido.",
            "de": "Alles fühlt sich sinnlos an.",
        },
        narratives={
            "en": "life feels meaningless. nothing feels meaningful anymore.",
            "uk": "життя здається meaningless. нічого не здається meaningful anymore.",
            "es": "la vida se siente sin sentido. nada se siente con significado.",
            "de": "life feels meaningless. nothing feels meaningful anymore.",
        },
    ),
    MultilingualCase(
        case_id="consistency_relationships",
        domain_label="Relationships",
        pattern_families=(
            frozenset(
                {
                    "trust_difficulty",
                    "fear_of_rejection",
                    "social_disconnection_signal",
                    "social_withdrawal",
                }
            ),
        ),
        primary_domain_fragments=("relationships_domain",),
        assessment_fragments=("relationships-domain",),
        primary_strategy_focus="relationships",
        presenting_problem={
            "en": "I want closeness but never let people get close.",
            "uk": "Хочу близькості, але не підпускаю людей.",
            "es": "Quiero cercanía pero no dejo acercarse a la gente.",
            "de": "Ich will Nähe, lasse aber niemanden nah heran.",
        },
        narratives={
            "en": (
                "It is hard for me to fully trust people. "
                "I keep emotional distance so I cannot be hurt."
            ),
            "uk": (
                "я нікому не потрібен. почуваюся відірваним від інших. "
                "не спілкуюсь з людьми."
            ),
            "es": (
                "Me cuesta confiar en la gente. Mantengo una distancia en las relaciones."
            ),
            "de": (
                "It is hard for me to fully trust people. "
                "I keep emotional distance so I cannot be hurt."
            ),
        },
    ),
    MultilingualCase(
        case_id="consistency_belonging",
        domain_label="Belonging",
        pattern_families=(
            frozenset({"social_disconnection_signal", "unworthiness_signal", "social_withdrawal"}),
        ),
        primary_domain_fragments=("relationships_domain", "self_domain"),
        assessment_fragments=("relationships-domain", "self-domain"),
        primary_strategy_focus="relationships",
        presenting_problem={
            "en": "I always feel like an outsider.",
            "uk": "Я завжди почуваюся чужим.",
            "es": "Siempre me siento como un extraño.",
            "de": "Ich fühle mich immer wie ein Außenseiter.",
        },
        narratives={
            "en": (
                "I feel like I do not belong. I feel disconnected from others. nobody needs me."
            ),
            "uk": (
                "наче я нікому не належу. почуваюся відірваним від інших. "
                "я нікому не потрібен."
            ),
            "es": (
                "siento que no pertenezco. me siento desconectado de los demás. "
                "siento que nadie me necesita."
            ),
            "de": (
                "I feel like I do not belong. I feel disconnected from others. nobody needs me."
            ),
        },
    ),
    MultilingualCase(
        case_id="consistency_emotion_regulation",
        domain_label="Emotion Regulation",
        pattern_families=(
            frozenset({"emotional_suppression", "emotional_overwhelm", "mental_overcontrol"}),
        ),
        primary_domain_fragments=("emotion_regulation_domain",),
        assessment_fragments=("emotion-regulation",),
        primary_strategy_focus="emotion regulation",
        presenting_problem={
            "en": "I suppress emotions until I suddenly explode.",
            "uk": "Я пригнічую емоції, поки не вибухаю.",
            "es": "Suprimo emociones hasta explotar.",
            "de": "Ich unterdrücke Emotionen, bis ich plötzlich explodiere.",
        },
        narratives={
            "en": (
                "I push my feelings down so I can keep going. "
                "I go numb when too much is happening."
            ),
            "uk": (
                "мушу тримати думки під контролем. "
                "постійно моніторю свій розум."
            ),
            "es": (
                "Suprimo mis sentimientos para poder seguir adelante. "
                "Me quedo entumecido cuando hay demasiado a la vez."
            ),
            "de": (
                "I push my feelings down so I can keep going. "
                "I go numb when too much is happening."
            ),
        },
    ),
    MultilingualCase(
        case_id="consistency_cognitive",
        domain_label="Cognitive Patterns",
        pattern_families=(
            frozenset({"rumination", "mental_overcontrol", "obsessive_thinking_loop"}),
        ),
        primary_domain_fragments=("cognitive_patterns_domain",),
        assessment_fragments=("cognitive-patterns",),
        primary_strategy_focus="personality / pacing",
        presenting_problem={
            "en": "I constantly overthink and cannot stop.",
            "uk": "Думки постійно крутяться в голові і я не можу зупинитися.",
            "es": "Pienso demasiado constantemente y no puedo parar.",
            "de": "Ich denke ständig zu viel nach und kann nicht aufhören.",
        },
        narratives={
            "en": (
                "My mind gets stuck on the same worries. "
                "I cannot stop thinking about what might happen."
            ),
            "uk": (
                "мушу тримати думки під контролем. "
                "постійно моніторю свій розум."
            ),
            "es": (
                "Mi mente se queda atascada en las mismas preocupaciones. "
                "No puedo dejar de pensar en lo que podría pasar."
            ),
            "de": (
                "My mind gets stuck on the same worries. "
                "I cannot stop thinking about what might happen."
            ),
        },
    ),
    MultilingualCase(
        case_id="consistency_anxiety",
        domain_label="Anxiety / Control",
        pattern_families=(
            frozenset({"fear_of_losing_control", "panic_reactivity", "control_resistance"}),
        ),
        primary_domain_fragments=("anxiety",),
        assessment_fragments=("anxiety",),
        primary_strategy_focus="emotion regulation",
        presenting_problem={
            "en": "I panic when things are not under control.",
            "uk": "Я панікую, коли все не під контролем.",
            "es": "Entro en pánico cuando todo no está bajo control.",
            "de": "Ich gerate in Panik, wenn nicht alles unter Kontrolle ist.",
        },
        narratives={
            "en": (
                "I'm afraid of losing control. panic hits me out of nowhere. "
                "I need to stay in control."
            ),
            "uk": (
                "я боюся втратити контроль. раптова паніка накриває мене. "
                "мені потрібно тримати все під контролем."
            ),
            "es": (
                "tengo miedo de perder el control. el pánico me golpea de la nada. "
                "necesito mantener el control."
            ),
            "de": (
                "I'm afraid of losing control. panic hits me out of nowhere. "
                "I need to stay in control."
            ),
        },
    ),
    MultilingualCase(
        case_id="consistency_values",
        domain_label="Values & Identity",
        pattern_families=(
            frozenset({"identity_confusion", "identity_uncertainty", "loss_of_meaning"}),
        ),
        primary_domain_fragments=("values_identity_domain",),
        assessment_fragments=("values-identity", "self-domain"),
        primary_strategy_focus="meaning / purpose",
        presenting_problem={
            "en": "I do not know what really matters to me anymore.",
            "uk": "Я не знаю, що для мене справді важливо.",
            "es": "Ya no sé qué me importa de verdad.",
            "de": "Ich weiß nicht mehr, was mir wirklich wichtig ist.",
        },
        narratives={
            "en": "I don't know who I am anymore. I feel confused about my identity.",
            "uk": "не знаю, хто я зараз. identity feels confused.",
            "es": "no sé quién soy ahora. me siento confundido sobre mi identidad.",
            "de": "I don't know who I am anymore. I feel confused about my identity.",
        },
    ),
    MultilingualCase(
        case_id="consistency_flexibility",
        domain_label="Emotional Flexibility",
        pattern_families=(
            frozenset(
                {
                    "emotional_avoidance",
                    "emotional_overwhelm",
                    "control_resistance",
                    "surrender_difficulty",
                }
            ),
        ),
        primary_domain_fragments=("emotion_regulation_domain", "emotional_flexibility_domain"),
        assessment_fragments=("emotional-flexibility", "emotion-regulation"),
        primary_strategy_focus="emotional flexibility",
        presenting_problem={
            "en": "I avoid difficult emotions or become overwhelmed.",
            "uk": "Я уникаю важких емоцій або переповнююсь.",
            "es": "Evito emociones difíciles o me abrumo.",
            "de": "Ich vermeide schwierige Emotionen oder werde überwältigt.",
        },
        narratives={
            "en": (
                "I avoid situations that might upset me. "
                "I get overwhelmed by my feelings quickly."
            ),
            "uk": (
                "я опираюся втраті контролю. мені потрібно тримати все під контролем."
            ),
            "es": (
                "Evito situaciones que podrían alterarme. "
                "Me abrumo con mis sentimientos rápidamente."
            ),
            "de": (
                "I avoid situations that might upset me. "
                "I get overwhelmed by my feelings quickly."
            ),
        },
    ),
)


@dataclass
class MultilingualArtifacts:
    case: MultilingualCase
    language: str
    profile: dict
    coverage_report: object
    fingerprint: dict
    strategy: object
    report_text: str
    strategy_text: str
    blueprint_text: str
    timeline_text: str
    selected_modules: list[str]
    completed_modules: list[str]
    detected_pattern_ids: set[str]


def _adaptive_answers() -> dict[str, dict[str, int]]:
    return {
        module_id: neutral_answers_for_module(module_id)
        for module_id in ALL_ASSESSMENT_MODULE_IDS
    }


def _intake_for_case(case: MultilingualCase, language: str) -> dict[str, str]:
    return {
        "presenting_problem": case.presenting_problem[language],
        **_INTAKE_TAIL[language],
    }


def run_multilingual_pipeline(case: MultilingualCase, language: str) -> MultilingualArtifacts:
    session = run_interview_session(
        intake_answers=_intake_for_case(case, language),
        user_inputs=[case.narratives[language]],
        turns=1,
        provider="mock",
        language=language,
        assessment=ASSESSMENT_ADAPTIVE,
        adaptive_assessment_answers=_adaptive_answers(),
        print_output=False,
    )

    profile = build_human_profile_summary(session.cumulative_pattern_tags)
    coverage_report = build_coverage_from_session(session)
    fingerprint = build_fingerprint_from_session(session)
    semantic_facts = []
    if session.intake_result is not None:
        semantic_facts = session.intake_result.evidence_store.facts()

    strategy = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=coverage_report,
    )
    report = build_human_profile_report_from_tags(
        session.cumulative_pattern_tags,
        presenting_problem=session.presenting_problem,
        assessment_module_runs=session.assessment_module_runs,
        semantic_facts=semantic_facts,
    )
    report_text = render_human_profile_report(report)
    strategy_text = render_intervention_strategy(strategy)
    blueprint = build_scenario_blueprint(profile, intervention_strategy=strategy)
    blueprint_text = render_scenario_blueprint(blueprint)
    timeline_text = render_session_timeline(simulate_session(profile))

    completed_modules = [run.module_id for run in session.assessment_module_runs]
    selection = select_assessment_modules(
        presenting_problem=session.presenting_problem,
        detected_patterns=session.cumulative_pattern_tags,
        semantic_facts=semantic_facts,
        completed_assessments={
            run.module_id: list(run.results) for run in session.assessment_module_runs
        },
    )

    return MultilingualArtifacts(
        case=case,
        language=language,
        profile=profile,
        coverage_report=coverage_report,
        fingerprint=fingerprint,
        strategy=strategy,
        report_text=report_text,
        strategy_text=strategy_text,
        blueprint_text=blueprint_text,
        timeline_text=timeline_text,
        selected_modules=list(selection.selected_modules),
        completed_modules=completed_modules,
        detected_pattern_ids={tag.canonical_id for tag in session.cumulative_pattern_tags},
    )


def _assert_no_diagnosis_language(*texts: str) -> None:
    combined = "\n".join(texts).lower()
    sanitized = re.sub(
        r"(descriptive, not diagnostic|non-diagnostic|without niros assigning a diagnosis|"
        r"without clinical diagnosis or naming a disorder|not a diagnosis|no diagnosis|"
        r"naming a disorder)",
        "",
        combined,
    )
    assert DIAGNOSIS_PATTERN.search(sanitized) is None
    assert "disorder" not in sanitized
    assert "clinical syndrome" not in sanitized


def _domain_level(coverage_report, fragment: str) -> str | None:
    for domain_id, domain in coverage_report.domains.items():
        if fragment in domain_id:
            return domain.level
    return None


def _domain_level_bucket(level: str | None) -> str:
    if level in {None, "unknown"}:
        return "weak"
    if level == "partial":
        return "partial"
    return "established"


def _all_modules(artifacts: MultilingualArtifacts) -> list[str]:
    return artifacts.completed_modules + artifacts.selected_modules


def _modules_include(module_ids: list[str], fragment: str) -> bool:
    return any(fragment in module_id for module_id in module_ids)


def _focus_confidence_map(strategy) -> dict[str, str]:
    return {item.focus_area: item.confidence for item in strategy.focus_confidence}


def _confidence_is_compatible(reference: str, other: str) -> bool:
    left = STRATEGY_CONFIDENCE_RANK.get(reference, 1)
    right = STRATEGY_CONFIDENCE_RANK.get(other, 1)
    return abs(left - right) <= 2


def _patterns_match_families(detected: set[str], families: tuple[frozenset[str], ...]) -> bool:
    return all(detected & family for family in families)


def _families_overlap(left: set[str], right: set[str], families: tuple[frozenset[str], ...]) -> bool:
    return all((left & family) and (right & family) for family in families)


def _domain_buckets_compatible(reference_bucket: str, other_bucket: str) -> bool:
    if reference_bucket == other_bucket:
        return True
    compatible_pairs = {
        frozenset({"established", "partial"}),
        frozenset({"partial", "weak"}),
    }
    return frozenset({reference_bucket, other_bucket}) in compatible_pairs


def _assert_language_artifacts_valid(artifacts: MultilingualArtifacts) -> None:
    assert artifacts.detected_pattern_ids
    assert _patterns_match_families(
        artifacts.detected_pattern_ids,
        artifacts.case.pattern_families,
    )
    assert artifacts.profile
    assert artifacts.coverage_report is not None
    assert artifacts.fingerprint["summary_text"]
    assert artifacts.strategy is not None
    assert _all_modules(artifacts)
    assert any(
        _modules_include(_all_modules(artifacts), fragment)
        for fragment in artifacts.case.assessment_fragments
    )
    _assert_no_diagnosis_language(
        artifacts.report_text,
        artifacts.strategy_text,
        artifacts.blueprint_text,
        artifacts.timeline_text,
    )


def _assert_consistent_with_reference(
    reference: MultilingualArtifacts,
    other: MultilingualArtifacts,
) -> None:
    assert _families_overlap(
        reference.detected_pattern_ids,
        other.detected_pattern_ids,
        reference.case.pattern_families,
    )

    compatible_domains = 0
    for fragment in reference.case.primary_domain_fragments:
        reference_bucket = _domain_level_bucket(_domain_level(reference.coverage_report, fragment))
        other_bucket = _domain_level_bucket(_domain_level(other.coverage_report, fragment))
        if _domain_buckets_compatible(reference_bucket, other_bucket):
            compatible_domains += 1
    assert compatible_domains >= 1

    assert any(
        _modules_include(_all_modules(reference), fragment)
        and _modules_include(_all_modules(other), fragment)
        for fragment in reference.case.assessment_fragments
    )

    reference_focus = _focus_confidence_map(reference.strategy)
    other_focus = _focus_confidence_map(other.strategy)
    primary_focus = reference.case.primary_strategy_focus
    assert primary_focus in reference_focus
    assert primary_focus in other_focus
    assert _confidence_is_compatible(reference_focus[primary_focus], other_focus[primary_focus])

    shared_focus = set(reference_focus) & set(other_focus)
    assert len(shared_focus) >= 2


@pytest.fixture(scope="module")
def multilingual_artifacts_by_case() -> dict[str, dict[str, MultilingualArtifacts]]:
    cache: dict[str, dict[str, MultilingualArtifacts]] = {}
    for case in MULTILINGUAL_CASES:
        cache[case.case_id] = {
            language: run_multilingual_pipeline(case, language)
            for language in LANGUAGES
        }
    return cache


def test_multilingual_suite_covers_four_languages_and_twelve_cases():
    assert LANGUAGES == ("en", "uk", "es", "de")
    assert len(MULTILINGUAL_CASES) == 12
    for case in MULTILINGUAL_CASES:
        assert set(case.presenting_problem) == set(LANGUAGES)
        assert set(case.narratives) == set(LANGUAGES)


@pytest.mark.parametrize("case", MULTILINGUAL_CASES, ids=[case.case_id for case in MULTILINGUAL_CASES])
@pytest.mark.parametrize("language", LANGUAGES)
def test_multilingual_case_runs_full_pipeline(
    case: MultilingualCase,
    language: str,
    multilingual_artifacts_by_case: dict[str, dict[str, MultilingualArtifacts]],
):
    artifacts = multilingual_artifacts_by_case[case.case_id][language]
    _assert_language_artifacts_valid(artifacts)


@pytest.mark.parametrize("case", MULTILINGUAL_CASES, ids=[case.case_id for case in MULTILINGUAL_CASES])
@pytest.mark.parametrize("language", LANGUAGES)
def test_multilingual_case_matches_reference_fingerprint(
    case: MultilingualCase,
    language: str,
    multilingual_artifacts_by_case: dict[str, dict[str, MultilingualArtifacts]],
):
    if language == REFERENCE_LANGUAGE:
        pytest.skip("reference language")

    reference = multilingual_artifacts_by_case[case.case_id][REFERENCE_LANGUAGE]
    other = multilingual_artifacts_by_case[case.case_id][language]
    _assert_consistent_with_reference(reference, other)


@pytest.mark.parametrize("case", MULTILINGUAL_CASES, ids=[case.case_id for case in MULTILINGUAL_CASES])
def test_multilingual_case_is_deterministic_per_language(case: MultilingualCase):
    for language in LANGUAGES:
        first = run_multilingual_pipeline(case, language)
        second = run_multilingual_pipeline(case, language)

        assert first.detected_pattern_ids == second.detected_pattern_ids
        assert first.completed_modules == second.completed_modules
        assert first.selected_modules == second.selected_modules
        assert first.strategy_text == second.strategy_text


def test_multilingual_self_case_ukrainian_and_spanish_align_with_english(
    multilingual_artifacts_by_case: dict[str, dict[str, MultilingualArtifacts]],
):
    reference = multilingual_artifacts_by_case["consistency_self"][REFERENCE_LANGUAGE]
    for language in ("uk", "es", "de"):
        _assert_consistent_with_reference(
            reference,
            multilingual_artifacts_by_case["consistency_self"][language],
        )
