from __future__ import annotations

from dataclasses import dataclass

from niros.knowledge import PatternLoader
from niros.patterns import PatternTag

SLEEP_PATTERN_IDS = frozenset({"sleep_disruption", "nightmare_disturbance", "insomnia_signal"})
BEREAVEMENT_PATTERN_IDS = frozenset({"bereavement_context"})
BREAKUP_PATTERN_IDS = frozenset(
    {
        "relationship_breakup_context",
        "attachment_loss_signal",
        "separation_distress",
        "abandonment_wound_signal",
    }
)
GRIEF_PATTERN_IDS = frozenset({"grief_signal", "loss_related_distress"})
ACCIDENT_PATTERN_IDS = frozenset({"accident_context", "trauma_context_signal", "post_event_distress"})
SOCIAL_PATTERN_IDS = frozenset({"social_withdrawal", "communication_avoidance"})
MEDICATION_PATTERN_IDS = frozenset(
    {
        "medication_history",
        "negative_medication_experience",
        "low_treatment_response_signal",
    }
)
FEAR_PANIC_PATTERN_IDS = frozenset(
    {
        "panic_reactivity",
        "generalized_fear",
        "fear_of_losing_control",
        "fear_of_death",
        "existential_fear",
        "safety_concern_signal",
    }
)

SLEEP_KEYWORDS = (
    "sleep",
    "insomnia",
    "сон",
    "спати",
    "заснути",
    "прокида",
    "sueño",
    "dormir",
    "сон наруш",
    "не могу спать",
    "майже не сплю",
    "проблеми зі сном",
)

GRIEF_KEYWORDS = (
    "смерт",
    "похорон",
    "скорбот",
    "bereavement",
    "mourning",
    "funeral",
    "died",
    "death",
    "lost someone",
    "muerte",
    "помер",
    "загин",
    "falleció",
    "murió",
    "умер",
    "погиб",
)

BREAKUP_KEYWORDS = (
    "розійш",
    "розрив",
    "расста",
    "разошл",
    "breakup",
    "broke up",
    "separated",
    "separation",
    "left me",
    "abandoned",
    "покинул",
    "бросил",
    "залишил",
    "terminé con",
    "me dejó",
    "ruptura",
    "separamos",
    "abandonó",
)

BEREAVEMENT_QUESTION_MARKERS = (
    "after this loss",
    "після цієї втрати",
    "после этой потери",
    "después de esta pérdida",
    "after that loss",
    "since that loss",
    "з того часу",
    "desde entonces",
)

ACCIDENT_KEYWORDS = (
    "автокатастроф",
    "авар",
    "дтп",
    "accident",
    "crash",
    "car crash",
    "traumatic event",
    "травматичн",
    "аварии",
    "accidente",
    "choque",
)

MEDICATION_KEYWORDS = (
    "антидепресант",
    "antidepressant",
    "medication",
    "ліки",
    "лекарств",
    "medicación",
    "antidepresivo",
    "prescribed",
    "призначили",
    "назначили",
    "recetaron",
)

SOCIAL_WITHDRAWAL_KEYWORDS = (
    "не спілкую",
    "уникаю людей",
    "avoid people",
    "don't socialize",
    "social withdrawal",
    "ні з ким не хочу",
    "не общаюсь",
    "evito a las personas",
)

GENERIC_FEAR_PANIC_MARKERS = (
    "страх або паніка",
    "fear or panic",
    "miedo o el pánico",
    "страх или паника",
)

DURATION_QUESTION_MARKERS = (
    "how long",
    "як довго",
    "как давно",
    "cuánto tiempo",
    "since when",
    "скільки часу",
)

CAUSE_QUESTION_MARKERS = (
    "what do you think contributed",
    "what may have contributed",
    "що могло сприяти",
    "что могло способствовать",
    "qué crees que pudo haber contribuido",
    "what contributed to",
)

GENERIC_SAY_MORE_MARKERS = (
    "can you say more",
    "можете сказати більше",
    "можете сказать больше",
    "puede decir más",
    "своими словами",
    "in your own words",
)

PATTERN_TOPIC_MAP: dict[str, str] = {
    "accident_context": "post_accident_changes",
    "trauma_context_signal": "post_accident_changes",
    "post_event_distress": "post_accident_changes",
    "sleep_disruption": "sleep_impact",
    "insomnia_signal": "sleep_impact",
    "nightmare_disturbance": "nightmare_content",
    "social_withdrawal": "social_withdrawal_inner_experience",
    "communication_avoidance": "social_withdrawal_inner_experience",
    "bereavement_context": "grief_context",
    "grief_signal": "grief_context",
    "loss_related_distress": "grief_context",
    "relationship_breakup_context": "breakup_impact",
    "attachment_loss_signal": "breakup_impact",
    "separation_distress": "separation_distress_context",
    "abandonment_wound_signal": "self_worth_after_rejection",
    "medication_history": "treatment_experience_detail",
    "negative_medication_experience": "treatment_experience_detail",
    "low_treatment_response_signal": "treatment_experience_detail",
    "depressed_mood_signal": "low_mood_timeline",
    "low_mood_signal": "low_mood_timeline",
    "desire_for_change": "change_goal_clarification",
    "recovery_goal_signal": "change_goal_clarification",
}


@dataclass(frozen=True)
class AdaptiveQuestionSpec:
    question_id: str
    topic_id: str
    texts: dict[str, str]
    target_patterns: frozenset[str]
    allow_repeat: bool = False


INTAKE_ADAPTIVE_QUESTIONS: tuple[AdaptiveQuestionSpec, ...] = (
    AdaptiveQuestionSpec(
        question_id="post_accident_changes_v1",
        topic_id="post_accident_changes",
        texts={
            "uk": "Що змінилося у вашому стані після автокатастрофи?",
            "en": "What changed most in how you feel after the accident?",
            "ru": "Что больше всего изменилось в вашем состоянии после аварии?",
            "es": "¿Qué cambió más en cómo te sientes después del accidente?",
        },
        target_patterns=ACCIDENT_PATTERN_IDS,
    ),
    AdaptiveQuestionSpec(
        question_id="sleep_impact_v1",
        topic_id="sleep_impact",
        texts={
            "uk": "Як саме порушення сну впливає на ваш день?",
            "en": "How exactly does poor sleep affect your day?",
            "ru": "Как именно нарушение сна влияет на ваш день?",
            "es": "¿Cómo afecta exactamente el sueño interrumpido a tu día?",
        },
        target_patterns=SLEEP_PATTERN_IDS,
    ),
    AdaptiveQuestionSpec(
        question_id="nightmare_content_v1",
        topic_id="nightmare_content",
        texts={
            "uk": "Що зазвичай відбувається у снах, які вас турбують?",
            "en": "What usually happens in the dreams that disturb you?",
            "ru": "Что обычно происходит в снах, которые вас тревожат?",
            "es": "¿Qué suele ocurrir en los sueños que le inquietan?",
        },
        target_patterns=frozenset({"nightmare_disturbance"}),
    ),
    AdaptiveQuestionSpec(
        question_id="social_withdrawal_inner_experience_v1",
        topic_id="social_withdrawal_inner_experience",
        texts={
            "uk": "Що відбувається всередині, коли ви уникаєте спілкування?",
            "en": "What happens inside when you avoid contact with others?",
            "ru": "Что происходит внутри, когда вы избегаете общения?",
            "es": "¿Qué ocurre por dentro cuando evitas el contacto con otros?",
        },
        target_patterns=SOCIAL_PATTERN_IDS,
    ),
    AdaptiveQuestionSpec(
        question_id="treatment_experience_detail_v1",
        topic_id="treatment_experience_detail",
        texts={
            "uk": "Що саме відчувалося не так під час прийому антидепресантів?",
            "en": "What felt wrong while you were taking the antidepressants?",
            "ru": "Что именно ощущалось не так во время приёма антидепрессантов?",
            "es": "¿Qué se sintió mal mientras tomaba los antidepresivos?",
        },
        target_patterns=MEDICATION_PATTERN_IDS,
    ),
    AdaptiveQuestionSpec(
        question_id="grief_context_v1",
        topic_id="grief_context",
        texts={
            "uk": "Що саме після цієї втрати найбільше змінило ваш стан?",
            "en": "What changed most in how you feel after this loss?",
            "ru": "Что больше всего изменило ваше состояние после этой потери?",
            "es": "¿Qué cambió más en cómo te sientes después de esta pérdida?",
        },
        target_patterns=BEREAVEMENT_PATTERN_IDS,
    ),
    AdaptiveQuestionSpec(
        question_id="breakup_impact_v1",
        topic_id="breakup_impact",
        texts={
            "uk": "Що найбільше змінилося у вашому стані після розриву?",
            "en": "What changed most in how you feel after the breakup?",
            "ru": "Что больше всего изменилось в вашем состоянии после расставания?",
            "es": "¿Qué cambió más en cómo se siente después de la ruptura?",
        },
        target_patterns=BREAKUP_PATTERN_IDS,
    ),
    AdaptiveQuestionSpec(
        question_id="separation_distress_context_v1",
        topic_id="separation_distress_context",
        texts={
            "uk": "Що в повсякденному житті зараз відчувається найважчим після розставання?",
            "en": "What part of daily life feels most affected since the separation?",
            "ru": "Что в повседневной жизни сейчас ощущается тяжелее после расставания?",
            "es": "¿Qué parte de la vida diaria se siente más afectada desde la separación?",
        },
        target_patterns=frozenset({"separation_distress", "attachment_loss_signal"}),
    ),
    AdaptiveQuestionSpec(
        question_id="self_worth_after_rejection_v1",
        topic_id="self_worth_after_rejection",
        texts={
            "uk": "Що відбувається всередині, коли відчуваєте, що вас залишили?",
            "en": "What happens inside when you feel left or abandoned?",
            "ru": "Что происходит внутри, когда вы чувствуете, что вас бросили?",
            "es": "¿Qué ocurre por dentro cuando siente que lo dejaron?",
        },
        target_patterns=frozenset({"abandonment_wound_signal", "rejection_sensitivity"}),
    ),
    AdaptiveQuestionSpec(
        question_id="change_goal_clarification_v1",
        topic_id="change_goal_clarification",
        texts={
            "uk": "Що для вас означало б відчувати себе краще?",
            "en": "What would feeling better mean for you?",
            "ru": "Что для вас означало бы чувствовать себя лучше?",
            "es": "¿Qué significaría para usted sentirse mejor?",
        },
        target_patterns=frozenset({"desire_for_change", "recovery_goal_signal"}),
    ),
    AdaptiveQuestionSpec(
        question_id="moments_of_relief_v1",
        topic_id="moments_of_relief",
        texts={
            "uk": "У які моменти зʼявляється хоча б трохи більше спокою?",
            "en": "In what moments do you feel even a little more calm?",
            "ru": "В какие моменты появляется хотя бы немного больше спокойствия?",
            "es": "¿En qué momentos aparece aunque sea un poco más de calma?",
        },
        target_patterns=frozenset(),
    ),
    AdaptiveQuestionSpec(
        question_id="sleep_bedtime_v1",
        topic_id="sleep_bedtime",
        texts={
            "uk": "Що зазвичай відбувається перед тим, як ви не можете заснути або прокидаєтесь?",
            "en": "What usually happens before you cannot fall asleep or you wake up?",
            "ru": "Что обычно происходит перед тем, как вы не можете заснуть или просыпаетесь?",
            "es": "¿Qué suele ocurrir antes de que no puedas dormirte o te despiertes?",
        },
        target_patterns=SLEEP_PATTERN_IDS,
    ),
)


def select_intake_targeted_question(
    *,
    presenting_problem: dict[str, str],
    pattern_tags: list[PatternTag],
    language: str,
    answered_questions: list[str],
    blocked_questions: list[str],
    answered_topics: list[str] | None = None,
    completed_topics: list[str] | None = None,
) -> str | None:
    detected = {tag.canonical_id for tag in pattern_tags}
    ranked_patterns = _rank_pattern_ids(pattern_tags)
    main_problem = presenting_problem.get("main_problem", "")
    perceived_causes = presenting_problem.get("perceived_causes", "")
    current_impact = presenting_problem.get("current_impact", "")
    previous_attempts = presenting_problem.get("previous_attempts", "")
    used_topics = merged_used_topics(
        answered_questions,
        answered_topics,
        completed_topics,
    )

    candidates: list[tuple[str, str | None, str | None, bool]] = []

    for spec in _ordered_intake_specs(
        detected=detected,
        main_problem=main_problem,
        perceived_causes=perceived_causes,
        current_impact=current_impact,
        previous_attempts=previous_attempts,
    ):
        candidates.append(
            (
                _localized_spec_text(spec, language),
                spec.question_id,
                spec.topic_id,
                spec.allow_repeat,
            )
        )

    for pattern_id in ranked_patterns:
        if _should_skip_pattern_follow_up(
            pattern_id,
            detected=detected,
            main_problem=main_problem,
            perceived_causes=perceived_causes,
            used_topics=used_topics,
        ):
            continue
        follow_up = _first_pattern_follow_up(pattern_id, language)
        if follow_up is not None and not _is_generic_say_more_question(follow_up):
            candidates.append(
                (
                    follow_up,
                    None,
                    PATTERN_TOPIC_MAP.get(pattern_id),
                    False,
                )
            )

    return _first_allowed_question(
        candidates,
        answered_questions,
        blocked_questions,
        used_topics,
    )


def extended_blocked_questions(
    *,
    presenting_problem: dict[str, str],
    pattern_tags: list[PatternTag],
    language: str,
    blocked_questions: list[str],
) -> list[str]:
    blocked = list(blocked_questions)
    blocked.extend(_generic_say_more_questions(language))

    if _intake_field_populated(presenting_problem, "duration"):
        blocked.extend(_questions_matching_markers(language, DURATION_QUESTION_MARKERS))

    if _intake_field_populated(presenting_problem, "perceived_causes"):
        blocked.extend(_questions_matching_markers(language, CAUSE_QUESTION_MARKERS))

    if not _fear_panic_is_central(
        {tag.canonical_id for tag in pattern_tags},
        presenting_problem.get("main_problem", ""),
        presenting_problem.get("perceived_causes", ""),
    ):
        for marker in GENERIC_FEAR_PANIC_MARKERS:
            blocked.append(marker)

        loader = PatternLoader()
        for pattern_id in ("emotional_distress_signal", "panic_reactivity", "generalized_fear"):
            pattern = loader.load(pattern_id)
            for question in _pattern_questions(pattern, language):
                if any(
                    marker in question.lower()
                    for marker in ("panic", "pani", "pánico", "паник", "страх")
                ):
                    blocked.append(question)

    if _breakup_is_present(
        {tag.canonical_id for tag in pattern_tags},
        presenting_problem.get("main_problem", ""),
        presenting_problem.get("perceived_causes", ""),
        presenting_problem.get("current_impact", ""),
    ):
        blocked.extend(_questions_matching_markers(language, BEREAVEMENT_QUESTION_MARKERS))
        loader = PatternLoader()
        for pattern_id in ("bereavement_context", "grief_signal", "loss_related_distress"):
            pattern = loader.load(pattern_id)
            for question in _pattern_questions(pattern, language):
                blocked.append(question)

    return _dedupe_preserve_order(blocked)


def is_generic_fear_panic_question(question: str) -> bool:
    lowered = question.lower()
    return any(marker in lowered for marker in GENERIC_FEAR_PANIC_MARKERS)


def is_question_already_asked(question: str, answered_questions: list[str]) -> bool:
    normalized = question.strip()
    return normalized in {item.strip() for item in answered_questions}


def is_topic_already_asked(topic_id: str, answered_topics: list[str]) -> bool:
    return topic_id in answered_topics


def topic_id_for_question(question: str) -> str | None:
    normalized = question.strip()
    for spec in INTAKE_ADAPTIVE_QUESTIONS:
        for text in spec.texts.values():
            if text.strip() == normalized:
                return spec.topic_id

    loader = PatternLoader()
    for pattern in loader.load_all():
        for questions in pattern.follow_up_questions.values():
            for follow_up in questions:
                if follow_up.strip() == normalized:
                    return PATTERN_TOPIC_MAP.get(pattern.canonical_id)
    return None


def question_id_for_question(question: str) -> str | None:
    normalized = question.strip()
    for spec in INTAKE_ADAPTIVE_QUESTIONS:
        for text in spec.texts.values():
            if text.strip() == normalized:
                return spec.question_id
    return None


def collect_answered_topics(answered_questions: list[str]) -> list[str]:
    topics: list[str] = []
    for question in answered_questions:
        topic_id = topic_id_for_question(question)
        if topic_id is not None and topic_id not in topics:
            topics.append(topic_id)
    return topics


def register_adaptive_answer(
    question: str,
    answer: str,
    *,
    answered_questions: list[str],
    completed_topics: list[str],
) -> None:
    normalized_question = question.strip()
    if normalized_question:
        existing = {item.strip() for item in answered_questions}
        if normalized_question not in existing:
            answered_questions.append(normalized_question)
    if answer.strip():
        topic_id = topic_id_for_question(question)
        if topic_id is not None and topic_id not in completed_topics:
            completed_topics.append(topic_id)


def _resolved_answered_topics(
    answered_questions: list[str],
    answered_topics: list[str] | None,
) -> list[str]:
    if answered_topics is not None:
        return list(answered_topics)
    return collect_answered_topics(answered_questions)


def merged_used_topics(
    answered_questions: list[str],
    answered_topics: list[str] | None,
    completed_topics: list[str] | None,
) -> list[str]:
    used = _resolved_answered_topics(answered_questions, answered_topics)
    if completed_topics is None:
        return used
    for topic_id in completed_topics:
        if topic_id not in used:
            used.append(topic_id)
    return used


def _ordered_intake_specs(
    *,
    detected: set[str],
    main_problem: str,
    perceived_causes: str,
    current_impact: str,
    previous_attempts: str,
) -> list[AdaptiveQuestionSpec]:
    ordered: list[AdaptiveQuestionSpec] = []
    spec_by_topic = {spec.topic_id: spec for spec in INTAKE_ADAPTIVE_QUESTIONS}

    if _mentions_accident(perceived_causes, main_problem, current_impact) or detected.intersection(
        ACCIDENT_PATTERN_IDS
    ):
        ordered.append(spec_by_topic["post_accident_changes"])

    if _mentions_sleep(main_problem, current_impact) or detected.intersection(SLEEP_PATTERN_IDS):
        ordered.append(spec_by_topic["sleep_impact"])

    if _mentions_social_withdrawal(main_problem, current_impact) or detected.intersection(
        SOCIAL_PATTERN_IDS
    ):
        ordered.append(spec_by_topic["social_withdrawal_inner_experience"])

    if _breakup_is_present(detected, main_problem, perceived_causes, current_impact):
        ordered.append(spec_by_topic["breakup_impact"])
        if detected.intersection({"separation_distress", "attachment_loss_signal"}):
            ordered.append(spec_by_topic["separation_distress_context"])
        if detected.intersection({"abandonment_wound_signal", "rejection_sensitivity"}):
            ordered.append(spec_by_topic["self_worth_after_rejection"])

    if (
        not _breakup_is_present(detected, main_problem, perceived_causes, current_impact)
        and (
            _mentions_bereavement(perceived_causes, main_problem)
            or detected.intersection(BEREAVEMENT_PATTERN_IDS)
        )
    ):
        ordered.append(spec_by_topic["grief_context"])

    if "nightmare_disturbance" in detected:
        ordered.append(spec_by_topic["nightmare_content"])

    if _mentions_medication(main_problem, current_impact, previous_attempts) or detected.intersection(
        MEDICATION_PATTERN_IDS
    ):
        ordered.append(spec_by_topic["treatment_experience_detail"])

    if _mentions_sleep(main_problem, current_impact) or detected.intersection(SLEEP_PATTERN_IDS):
        ordered.append(spec_by_topic["sleep_bedtime"])

    ordered.append(spec_by_topic["moments_of_relief"])
    return ordered


def _first_allowed_question(
    candidates: list[tuple[str, str | None, str | None, bool]],
    answered_questions: list[str],
    blocked_questions: list[str],
    answered_topics: list[str],
) -> str | None:
    blocked = set(blocked_questions)
    seen_questions: set[str] = set()
    answered_question_ids = {
        item for item in (question_id_for_question(q) for q in answered_questions) if item
    }
    for question, question_id, topic_id, allow_repeat in candidates:
        if question in seen_questions or question in blocked:
            continue
        if is_question_already_asked(question, answered_questions):
            continue
        if question_id is not None and question_id in answered_question_ids:
            continue
        if topic_id is not None and not allow_repeat and is_topic_already_asked(topic_id, answered_topics):
            continue
        seen_questions.add(question)
        return question
    return None


def _localized_spec_text(spec: AdaptiveQuestionSpec, language: str) -> str:
    return spec.texts.get(language, spec.texts["en"])


def _intake_field_populated(presenting_problem: dict[str, str], field: str) -> bool:
    return bool(str(presenting_problem.get(field, "")).strip())


def _mentions_sleep(*texts: str) -> bool:
    combined = " ".join(text.lower() for text in texts if text)
    return any(keyword in combined for keyword in SLEEP_KEYWORDS)


def _mentions_bereavement(*texts: str) -> bool:
    combined = " ".join(text.lower() for text in texts if text)
    return any(keyword in combined for keyword in GRIEF_KEYWORDS)


def _mentions_breakup(*texts: str) -> bool:
    combined = " ".join(text.lower() for text in texts if text)
    return any(keyword in combined for keyword in BREAKUP_KEYWORDS)


def _breakup_is_present(
    detected: set[str],
    main_problem: str,
    perceived_causes: str,
    current_impact: str,
) -> bool:
    if detected.intersection(BREAKUP_PATTERN_IDS):
        return True
    return _mentions_breakup(main_problem, perceived_causes, current_impact)


def _mentions_accident(*texts: str) -> bool:
    combined = " ".join(text.lower() for text in texts if text)
    return any(keyword in combined for keyword in ACCIDENT_KEYWORDS)


def _mentions_medication(*texts: str) -> bool:
    combined = " ".join(text.lower() for text in texts if text)
    return any(keyword in combined for keyword in MEDICATION_KEYWORDS)


def _mentions_social_withdrawal(*texts: str) -> bool:
    combined = " ".join(text.lower() for text in texts if text)
    return any(keyword in combined for keyword in SOCIAL_WITHDRAWAL_KEYWORDS)


def _fear_panic_is_central(
    detected: set[str],
    main_problem: str,
    perceived_causes: str,
) -> bool:
    if detected.intersection(FEAR_PANIC_PATTERN_IDS):
        return True

    combined = f"{main_problem} {perceived_causes}".lower()
    fear_markers = ("страх", "panic", "пані", "fear", "miedo", "боюся", "боюсь", "паник")
    return any(marker in combined for marker in fear_markers)


def _should_skip_pattern_follow_up(
    pattern_id: str,
    *,
    detected: set[str],
    main_problem: str,
    perceived_causes: str,
    used_topics: list[str],
) -> bool:
    topic_id = PATTERN_TOPIC_MAP.get(pattern_id)
    if topic_id is not None and is_topic_already_asked(topic_id, used_topics):
        return True
    if pattern_id in {"grief_signal", "loss_related_distress", "bereavement_context"}:
        if is_topic_already_asked("grief_context", used_topics):
            return True
    if pattern_id in BREAKUP_PATTERN_IDS:
        topic_id = PATTERN_TOPIC_MAP.get(pattern_id)
        if topic_id is not None and is_topic_already_asked(topic_id, used_topics):
            return True
    if pattern_id in {"depressed_mood_signal", "low_mood_signal", "anxiety_reactivity"}:
        return True
    if pattern_id in ACCIDENT_PATTERN_IDS and is_topic_already_asked("post_accident_changes", used_topics):
        return True
    if pattern_id in MEDICATION_PATTERN_IDS and is_topic_already_asked(
        "treatment_experience_detail", used_topics
    ):
        return True
    if pattern_id == "emotional_distress_signal" and not _fear_panic_is_central(
        detected,
        main_problem,
        perceived_causes,
    ):
        return True
    if pattern_id in FEAR_PANIC_PATTERN_IDS and not _fear_panic_is_central(
        detected,
        main_problem,
        perceived_causes,
    ):
        return True
    return False


def _is_generic_say_more_question(question: str) -> bool:
    lowered = question.lower()
    return any(marker in lowered for marker in GENERIC_SAY_MORE_MARKERS)


def _questions_matching_markers(language: str, markers: tuple[str, ...]) -> list[str]:
    loader = PatternLoader()
    matched: list[str] = []
    for pattern in loader.load_all():
        for question in _pattern_questions(pattern, language):
            lowered = question.lower()
            if any(marker in lowered for marker in markers):
                matched.append(question)
    return matched


def _generic_say_more_questions(language: str) -> list[str]:
    return _questions_matching_markers(language, GENERIC_SAY_MORE_MARKERS)


def _pattern_questions(pattern, language: str) -> list[str]:
    questions = list(pattern.follow_up_questions.get(language, []))
    questions.extend(pattern.follow_up_questions.get("en", []))
    return questions


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _rank_pattern_ids(pattern_tags: list[PatternTag]) -> list[str]:
    loader = PatternLoader()
    priorities = {pattern.canonical_id: pattern.interview_priority for pattern in loader.load_all()}
    best_confidence: dict[str, float] = {}
    for tag in pattern_tags:
        current = best_confidence.get(tag.canonical_id, 0.0)
        if tag.confidence > current:
            best_confidence[tag.canonical_id] = tag.confidence

    return sorted(
        best_confidence,
        key=lambda pattern_id: (-priorities.get(pattern_id, 0), -best_confidence[pattern_id], pattern_id),
    )


def _first_pattern_follow_up(pattern_id: str, language: str) -> str | None:
    loader = PatternLoader()
    pattern = loader.load(pattern_id)
    questions = pattern.follow_up_questions.get(language) or pattern.follow_up_questions.get("en", [])
    if not questions:
        return None
    return questions[0]
