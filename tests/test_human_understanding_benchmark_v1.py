"""Human Understanding Benchmark v1 — behavioral quality gate for HLU pipeline.

Checks whether NIROS interprets natural language carefully:
identifies possible meanings, asks when uncertain, and avoids premature conclusions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

import pytest

from niros.human_language_understanding_pipeline import (
    HumanLanguageUnderstandingPipeline,
    HumanLanguageUnderstandingResult,
)
from niros.semantic_interpreter.facts import SemanticFact

FORBIDDEN_DIAGNOSTIC_TERMS = (
    "diagnosis",
    "disorder",
    "pathology",
    "symptom severity",
    "patient has",
    "clinically indicates",
)

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(?:is|e|ed|ing)|disorder|patholog(?:y|ical)|clinical disorder)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class HumanUnderstandingBenchmarkCase:
    case_id: str
    input_text: str
    language: str
    expected_candidate_concepts: tuple[str, ...] = ()
    expected_accepted_concepts: tuple[str, ...] = ()
    expected_open_question_concepts: tuple[str, ...] = ()
    should_need_clarification: bool | None = None
    forbidden_terms: tuple[str, ...] = FORBIDDEN_DIAGNOSTIC_TERMS
    patterns: tuple[str, ...] = ()
    semantic_facts: tuple[SemanticFact, ...] = ()
    require_open_questions: bool = False
    require_candidate_signals: bool = False
    multilingual_stable: bool = False


def _pipeline() -> HumanLanguageUnderstandingPipeline:
    return HumanLanguageUnderstandingPipeline()


def _run_case(case: HumanUnderstandingBenchmarkCase) -> HumanLanguageUnderstandingResult:
    return _pipeline().run(
        text=case.input_text,
        language=case.language,
        patterns=list(case.patterns) if case.patterns else None,
        semantic_facts=list(case.semantic_facts) if case.semantic_facts else None,
    )


def _all_signal_names(result: HumanLanguageUnderstandingResult) -> set[str]:
    names = {node.signal_type for node in result.semantic_signal_graph.nodes}
    names.update(item.signal for item in result.accepted_signals)
    names.update(item.signal for item in result.candidate_signals)
    return names


def _candidate_signal_names(result: HumanLanguageUnderstandingResult) -> set[str]:
    return {item.signal for item in result.candidate_signals}


def _accepted_signal_names(result: HumanLanguageUnderstandingResult) -> set[str]:
    return {item.signal for item in result.accepted_signals}


def _question_text(result: HumanLanguageUnderstandingResult) -> str:
    chunks = [item.question for item in result.open_questions]
    chunks.extend(item.question for item in result.interview_questions)
    return " ".join(chunks)


def _result_blob(result: HumanLanguageUnderstandingResult) -> str:
    return str(result.to_dict()).lower()


def _matches_concepts(names: Iterable[str], concepts: tuple[str, ...]) -> bool:
    if not concepts:
        return True
    lowered = [name.lower() for name in names]
    return any(any(concept.lower() in name for name in lowered) for concept in concepts)


def _assert_common_expectations(case: HumanUnderstandingBenchmarkCase, result: HumanLanguageUnderstandingResult) -> None:
    assert result.semantic_signal_graph is not None
    assert result.semantic_signal_graph.original_text == case.input_text.strip()
    assert result.semantic_signal_graph.evidence
    assert result.semantic_signal_graph.evidence[0].text == case.input_text.strip()
    assert result.semantic_signal_graph.evidence[0].language == case.language

    blob = _result_blob(result)
    assert DIAGNOSIS_PATTERN.search(blob) is None
    for term in case.forbidden_terms:
        assert term not in blob

    duplicate = _run_case(case)
    assert duplicate == result
    assert duplicate.to_dict() == result.to_dict()


def _assert_ambiguous_expectations(case: HumanUnderstandingBenchmarkCase, result: HumanLanguageUnderstandingResult) -> None:
    assert result.needs_clarification is True

    if case.require_candidate_signals or case.expected_candidate_concepts:
        assert result.candidate_signals or result.semantic_signal_graph.candidate_nodes()

    if case.expected_candidate_concepts:
        assert _matches_concepts(_all_signal_names(result), case.expected_candidate_concepts)

    accepted = _accepted_signal_names(result)
    for concept in case.expected_candidate_concepts:
        assert not any(concept.lower() in signal.lower() for signal in accepted)

    if case.require_open_questions:
        assert result.open_questions or result.interview_questions
        assert _matches_concepts([_question_text(result)], case.expected_open_question_concepts)

    if case.expected_open_question_concepts:
        assert _matches_concepts([_question_text(result)], case.expected_open_question_concepts)


def _assert_clear_expectations(case: HumanUnderstandingBenchmarkCase, result: HumanLanguageUnderstandingResult) -> None:
    if case.should_need_clarification is False:
        assert result.needs_clarification is False

    if case.expected_accepted_concepts:
        assert _matches_concepts(_accepted_signal_names(result), case.expected_accepted_concepts)

    if case.expected_open_question_concepts:
        assert _matches_concepts([_question_text(result)], case.expected_open_question_concepts)


BENCHMARK_CASES: tuple[HumanUnderstandingBenchmarkCase, ...] = (
    HumanUnderstandingBenchmarkCase(
        case_id="uk_living_not_own_life",
        input_text="Я живу не своїм життям.",
        language="uk",
        patterns=("identity_confusion", "identity_uncertainty"),
        expected_candidate_concepts=("identity",),
        should_need_clarification=True,
        require_candidate_signals=True,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="en_living_someone_elses_life",
        input_text="I feel like I am living someone else's life.",
        language="en",
        expected_candidate_concepts=("identity", "values", "agency", "meaning"),
        should_need_clarification=True,
        require_candidate_signals=True,
        require_open_questions=True,
        expected_open_question_concepts=("someone else's life", "values"),
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="uk_helpful_but_empty_inside",
        input_text="Я всім допомагаю, але всередині порожньо.",
        language="uk",
        patterns=("harsh_self_criticism",),
        semantic_facts=(
            SemanticFact(
                category="self",
                attribute="unworthiness",
                value="present",
                evidence="Я всім допомагаю, але всередині порожньо.",
            ),
        ),
        expected_candidate_concepts=("self", "worth", "self_criticism"),
        should_need_clarification=True,
        require_candidate_signals=True,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="en_constant_self_criticism",
        input_text="I constantly criticize myself even when I do well.",
        language="en",
        expected_candidate_concepts=("self_criticism", "self_worth", "shame"),
        expected_accepted_concepts=(),
        should_need_clarification=True,
        require_candidate_signals=True,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="uk_grief_mother_future_loss",
        input_text="Після смерті мами я ніби перестав відчувати майбутнє.",
        language="uk",
        patterns=("grief_signal",),
        semantic_facts=(
            SemanticFact(
                category="life_event",
                attribute="bereavement",
                value="present",
                evidence="Після смерті мами",
            ),
            SemanticFact(
                category="meaning",
                attribute="meaning_sense",
                value="reduced",
                evidence="перестав відчувати майбутнє",
            ),
        ),
        expected_candidate_concepts=("grief", "meaning"),
        should_need_clarification=True,
        require_candidate_signals=True,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="uk_conditional_worth_if_not_useful",
        input_text="Мені здається, що якщо я перестану бути корисним, мене ніхто не любитиме.",
        language="uk",
        patterns=("harsh_self_criticism", "shame_sensitivity"),
        semantic_facts=(
            SemanticFact(
                category="self",
                attribute="unworthiness",
                value="present",
                evidence="якщо я перестану бути корисним",
            ),
            SemanticFact(
                category="relationship",
                attribute="fear_of_rejection",
                value="present",
                evidence="мене ніхто не любитиме",
            ),
        ),
        expected_candidate_concepts=("self", "worth", "self_criticism", "shame"),
        should_need_clarification=True,
        require_candidate_signals=True,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="en_atheist_religion_averse",
        input_text="I do not believe in God and religious language makes me uncomfortable.",
        language="en",
        expected_accepted_concepts=("worldview", "religion", "symbolic"),
        should_need_clarification=False,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="uk_spiritual_not_religious_nature",
        input_text="Я не релігійний, але коли дивлюся на гори, відчуваю щось велике.",
        language="uk",
        patterns=("meaning_seeking", "spiritual_openness"),
        multilingual_stable=True,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="de_rumination_cannot_switch_off",
        input_text="Ich denke ständig über alles nach und kann nicht abschalten.",
        language="de",
        patterns=("harsh_self_criticism",),
        multilingual_stable=True,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="es_not_belonging_anywhere",
        input_text="Siento que no pertenezco a ningún lugar.",
        language="es",
        patterns=("harsh_self_criticism",),
        semantic_facts=(
            SemanticFact(
                category="self",
                attribute="unworthiness",
                value="present",
                evidence="no pertenezco a ningún lugar",
            ),
        ),
        expected_candidate_concepts=("self", "worth", "self_criticism"),
        should_need_clarification=True,
        require_candidate_signals=True,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="uk_good_on_outside_hate_self_inside",
        input_text="Я ніби хороший, але ненавиджу себе.",
        language="uk",
        patterns=("harsh_self_criticism", "shame_sensitivity"),
        expected_candidate_concepts=("self_criticism", "shame"),
        should_need_clarification=True,
        require_candidate_signals=True,
    ),
    HumanUnderstandingBenchmarkCase(
        case_id="en_agnostic_spiritual_language_caution",
        input_text=(
            "I don't know what I believe, but I don't want anyone forcing spiritual language on me."
        ),
        language="en",
        patterns=("spiritual_resistance", "identity_uncertainty"),
        expected_candidate_concepts=("worldview", "religion", "symbolic", "identity"),
        should_need_clarification=True,
        require_candidate_signals=True,
    ),
)


@pytest.mark.parametrize("case", BENCHMARK_CASES, ids=[case.case_id for case in BENCHMARK_CASES])
def test_human_understanding_benchmark_case(case: HumanUnderstandingBenchmarkCase) -> None:
    result = _run_case(case)
    _assert_common_expectations(case, result)

    if case.should_need_clarification is True:
        _assert_ambiguous_expectations(case, result)
    elif case.should_need_clarification is False:
        _assert_clear_expectations(case, result)
    else:
        if case.expected_candidate_concepts:
            assert _matches_concepts(_all_signal_names(result), case.expected_candidate_concepts)
        if case.expected_accepted_concepts:
            assert _matches_concepts(_accepted_signal_names(result), case.expected_accepted_concepts)

    if case.multilingual_stable:
        assert result.semantic_signal_graph.language == case.language


def test_human_understanding_benchmark_has_twelve_cases() -> None:
    assert len(BENCHMARK_CASES) == 12


def test_human_understanding_benchmark_preserves_evidence_for_all_cases() -> None:
    for case in BENCHMARK_CASES:
        result = _run_case(case)
        assert any(case.input_text in item.text for item in result.semantic_signal_graph.evidence)


def test_human_understanding_benchmark_avoids_premature_acceptance_on_ambiguous_cases() -> None:
    ambiguous_cases = [case for case in BENCHMARK_CASES if case.should_need_clarification is True]
    assert len(ambiguous_cases) >= 8

    for case in ambiguous_cases:
        result = _run_case(case)
        if not case.expected_candidate_concepts:
            continue
        accepted = _accepted_signal_names(result)
        for concept in case.expected_candidate_concepts:
            assert not any(concept.lower() in signal.lower() for signal in accepted)


def test_human_understanding_benchmark_clear_cases_can_accept_high_confidence_signals() -> None:
    result = _run_case(BENCHMARK_CASES[6])
    assert _accepted_signal_names(result)
    assert result.needs_clarification is False


def test_human_understanding_benchmark_self_criticism_keeps_signals_in_proposals_not_fingerprint() -> None:
    result = _run_case(BENCHMARK_CASES[3])
    signals = _all_signal_names(result)
    assert _matches_concepts(signals, ("self_criticism", "self_worth", "shame"))
    assert result.fingerprint_update_proposal is not None
    assert isinstance(result.to_dict()["fingerprint_update_proposal"], dict)
