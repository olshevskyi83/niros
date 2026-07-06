"""Guided Assessment — deterministic intake mapping for the NIROS workstation."""

from __future__ import annotations

from dataclasses import dataclass, field

from niros.pattern_person_fit_contracts import PersonFitProfile
from niros.ui_human_readable import LANG_EN, LANG_ES, LANG_UK, normalize_language

WORKSTATION_MODE_GUIDED = "guided_assessment"
WORKSTATION_MODE_QUICK_DEMO = "quick_demo"

INPUT_MODE_GUIDED = "guided_assessment"

INITIAL_QUESTION_KEY = "initial_statement"

QUESTION_KEYS: tuple[str, ...] = (
    "q_difficult",
    "q_coping",
    "q_emotion",
    "q_self_talk",
    "q_need",
    "q_risk",
)

ALL_ANSWER_KEYS: tuple[str, ...] = (INITIAL_QUESTION_KEY,) + QUESTION_KEYS

COVERAGE_KEYS: tuple[str, ...] = (
    "initial_statement",
    "emotional_pattern",
    "coping_avoidance",
    "self_talk",
    "need",
    "risk",
)

COVERAGE_TO_ANSWER_KEY: dict[str, str] = {
    "initial_statement": INITIAL_QUESTION_KEY,
    "emotional_pattern": "q_emotion",
    "coping_avoidance": "q_coping",
    "self_talk": "q_self_talk",
    "need": "q_need",
    "risk": "q_risk",
}

QUESTION_TEXT: dict[str, dict[str, str]] = {
    INITIAL_QUESTION_KEY: {
        LANG_EN: "What brings you here today?",
        LANG_UK: "Що привело вас сюди сьогодні?",
        LANG_ES: "What brings you here today?",
    },
    "q_difficult": {
        LANG_EN: "What feels most difficult right now?",
        LANG_UK: "Що зараз відчувається найважчим?",
        LANG_ES: "What feels most difficult right now?",
    },
    "q_coping": {
        LANG_EN: "When this happens, what do you usually do internally or externally?",
        LANG_UK: "Коли це трапляється, що ви зазвичай робите всередині або назовні?",
        LANG_ES: "When this happens, what do you usually do internally or externally?",
    },
    "q_emotion": {
        LANG_EN: "What emotion is hardest to stay with?",
        LANG_UK: "З якою емоцією найважче залишатися?",
        LANG_ES: "What emotion is hardest to stay with?",
    },
    "q_self_talk": {
        LANG_EN: "How do you usually talk to yourself in these moments?",
        LANG_UK: "Як ви зазвичай говорите з собою в такі моменти?",
        LANG_ES: "How do you usually talk to yourself in these moments?",
    },
    "q_need": {
        LANG_EN: (
            "What do you most need from this session: stabilization, self-compassion, "
            "clarity, emotional tolerance, or direction?"
        ),
        LANG_UK: (
            "Що вам найбільше потрібно від цієї сесії: стабілізація, самоспівчуття, "
            "ясність, емоційна толерантність чи напрямок?"
        ),
        LANG_ES: (
            "What do you most need from this session: stabilization, self-compassion, "
            "clarity, emotional tolerance, or direction?"
        ),
    },
    "q_risk": {
        LANG_EN: "Is there any risk of feeling overwhelmed if we go too deep too fast?",
        LANG_UK: "Чи є ризик почуватися перевантаженим, якщо йти занадто глибоко занадто швидко?",
        LANG_ES: "Is there any risk of feeling overwhelmed if we go too deep too fast?",
    },
}

COVERAGE_LABELS: dict[str, dict[str, str]] = {
    "initial_statement": {
        LANG_EN: "Initial statement collected",
        LANG_UK: "Початкову заяву зібрано",
        LANG_ES: "Initial statement collected",
    },
    "emotional_pattern": {
        LANG_EN: "Emotional pattern collected",
        LANG_UK: "Емоційний патерн зібрано",
        LANG_ES: "Emotional pattern collected",
    },
    "coping_avoidance": {
        LANG_EN: "Coping/avoidance collected",
        LANG_UK: "Копінг/уникання зібрано",
        LANG_ES: "Coping/avoidance collected",
    },
    "self_talk": {
        LANG_EN: "Self-talk collected",
        LANG_UK: "Внутрішній діалог зібрано",
        LANG_ES: "Self-talk collected",
    },
    "need": {
        LANG_EN: "Need collected",
        LANG_UK: "Потребу зібрано",
        LANG_ES: "Need collected",
    },
    "risk": {
        LANG_EN: "Risk collected",
        LANG_UK: "Ризик зібрано",
        LANG_ES: "Risk collected",
    },
}

INSUFFICIENT_COVERAGE_MESSAGE: dict[str, str] = {
    LANG_EN: "NIROS does not have enough signal coverage yet. Please answer more specifically.",
    LANG_UK: "NIROS ще не має достатнього покриття сигналів. Будь ласка, відповідайте конкретніше.",
    LANG_ES: "NIROS does not have enough signal coverage yet. Please answer more specifically.",
}

WORKSTATION_UI: dict[str, dict[str, str]] = {
    "workstation_mode": {
        LANG_EN: "Workstation mode",
        LANG_UK: "Режим робочої станції",
        LANG_ES: "Workstation mode",
    },
    "guided_assessment": {
        LANG_EN: "Guided Assessment",
        LANG_UK: "Керована оцінка",
        LANG_ES: "Guided Assessment",
    },
    "quick_demo": {
        LANG_EN: "Quick Demo",
        LANG_UK: "Швидке демо",
        LANG_ES: "Quick Demo",
    },
    "demo_warning": {
        LANG_EN: (
            "Demo mode uses simplified mock semantic mapping and should not be treated "
            "as a full NIROS assessment."
        ),
        LANG_UK: (
            "Демо-режим використовує спрощене імітаційне семантичне зіставлення і не "
            "повинен сприйматися як повна оцінка NIROS."
        ),
        LANG_ES: (
            "Demo mode uses simplified mock semantic mapping and should not be treated "
            "as a full NIROS assessment."
        ),
    },
    "guided_intake": {
        LANG_EN: "Guided intake",
        LANG_UK: "Керований intake",
        LANG_ES: "Guided intake",
    },
    "coverage_status": {
        LANG_EN: "Coverage status",
        LANG_UK: "Стан покриття",
        LANG_ES: "Coverage status",
    },
    "generate_fingerprint_strategy": {
        LANG_EN: "Generate Fingerprint & Strategy",
        LANG_UK: "Згенерувати Fingerprint і стратегію",
        LANG_ES: "Generate Fingerprint & Strategy",
    },
    "complete_all_questions": {
        LANG_EN: "Answer all guided questions to continue.",
        LANG_UK: "Відповідайте на всі керовані запитання, щоб продовжити.",
        LANG_ES: "Answer all guided questions to continue.",
    },
    "step_initial": {
        LANG_EN: "Step 1 — Initial statement",
        LANG_UK: "Крок 1 — Початкова заява",
        LANG_ES: "Step 1 — Initial statement",
    },
    "step_clarification": {
        LANG_EN: "Step 2 — Clarification questions",
        LANG_UK: "Крок 2 — Уточнювальні запитання",
        LANG_ES: "Step 2 — Clarification questions",
    },
    "collected": {
        LANG_EN: "Collected",
        LANG_UK: "Зібрано",
        LANG_ES: "Collected",
    },
    "pending": {
        LANG_EN: "Pending",
        LANG_UK: "Очікується",
        LANG_ES: "Pending",
    },
}

SHAME_KEYWORDS = ("shame", "sorry", "not enough", "щось не так", "сором")
CRITIC_KEYWORDS = ("critic", "критик", "самокрит", "жорстко")
AVOID_KEYWORDS = ("avoid", "уникаю", "не відчувати", "escape")
OVERWHELM_KEYWORDS = ("overwhelm", "накриває", "занадто", "too much", "перевантаж")


@dataclass(frozen=True)
class GuidedAssessmentAnswers:
    initial_statement: str = ""
    q_difficult: str = ""
    q_coping: str = ""
    q_emotion: str = ""
    q_self_talk: str = ""
    q_need: str = ""
    q_risk: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            INITIAL_QUESTION_KEY: self.initial_statement,
            "q_difficult": self.q_difficult,
            "q_coping": self.q_coping,
            "q_emotion": self.q_emotion,
            "q_self_talk": self.q_self_talk,
            "q_need": self.q_need,
            "q_risk": self.q_risk,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> GuidedAssessmentAnswers:
        return cls(
            initial_statement=data.get(INITIAL_QUESTION_KEY, ""),
            q_difficult=data.get("q_difficult", ""),
            q_coping=data.get("q_coping", ""),
            q_emotion=data.get("q_emotion", ""),
            q_self_talk=data.get("q_self_talk", ""),
            q_need=data.get("q_need", ""),
            q_risk=data.get("q_risk", ""),
        )


@dataclass(frozen=True)
class CoverageStatus:
    key: str
    label: str
    collected: bool


@dataclass(frozen=True)
class GuidedProfileResult:
    profile: PersonFitProfile | None
    insufficient_coverage: bool
    active_signals: tuple[str, ...] = field(default_factory=tuple)
    needs: tuple[str, ...] = field(default_factory=tuple)


def question_text(key: str, language: str) -> str:
    """Return localized question text."""
    lang = normalize_language(language)
    texts = QUESTION_TEXT.get(key, {})
    return texts.get(lang) or texts.get(LANG_EN, key)


def coverage_label(key: str, language: str) -> str:
    """Return localized coverage status label."""
    lang = normalize_language(language)
    labels = COVERAGE_LABELS.get(key, {})
    return labels.get(lang) or labels.get(LANG_EN, key)


def insufficient_coverage_message(language: str) -> str:
    lang = normalize_language(language)
    return INSUFFICIENT_COVERAGE_MESSAGE.get(lang) or INSUFFICIENT_COVERAGE_MESSAGE[LANG_EN]


def workstation_ui_text(key: str, language: str) -> str:
    """Return localized workstation-mode UI copy."""
    lang = normalize_language(language)
    labels = WORKSTATION_UI.get(key, {})
    return labels.get(lang) or labels.get(LANG_EN, key)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def combined_answer_text(answers: GuidedAssessmentAnswers) -> str:
    """Combine all guided answers into one corpus for keyword mapping."""
    parts = [
        answers.initial_statement,
        answers.q_difficult,
        answers.q_coping,
        answers.q_emotion,
        answers.q_self_talk,
        answers.q_need,
        answers.q_risk,
    ]
    return "\n".join(part.strip() for part in parts if part.strip())


def build_coverage_status(
    answers: GuidedAssessmentAnswers,
    language: str,
) -> tuple[CoverageStatus, ...]:
    """Return coverage progress for each required intake area."""
    answer_map = answers.as_dict()
    statuses: list[CoverageStatus] = []
    for key in COVERAGE_KEYS:
        answer_key = COVERAGE_TO_ANSWER_KEY[key]
        collected = bool(answer_map.get(answer_key, "").strip())
        if key == "initial_statement":
            collected = bool(answers.initial_statement.strip())
        statuses.append(
            CoverageStatus(
                key=key,
                label=coverage_label(key, language),
                collected=collected,
            )
        )
    return tuple(statuses)


def all_required_answers_collected(answers: GuidedAssessmentAnswers) -> bool:
    """Return True when every guided question has a non-empty answer."""
    data = answers.as_dict()
    return all(bool(data.get(key, "").strip()) for key in ALL_ANSWER_KEYS)


def build_transcript(answers: GuidedAssessmentAnswers, language: str) -> str:
    """Build a Question/Answer transcript from guided intake answers."""
    lang = normalize_language(language)
    blocks: list[str] = []
    for key in ALL_ANSWER_KEYS:
        question = question_text(key, lang)
        answer = answers.as_dict().get(key, "").strip()
        blocks.append(f"Question: {question}\nAnswer: {answer}")
    return "\n\n".join(blocks)


def _infer_dominant_domains(active_signals: tuple[str, ...]) -> tuple[str, ...]:
    domains: list[str] = []
    if any(signal in active_signals for signal in ("shame_sensitivity", "harsh_self_criticism")):
        domains.append("self")
    if any(
        signal in active_signals
        for signal in ("emotional_avoidance", "overwhelm_risk")
    ):
        domains.append("emotion_regulation")
    return tuple(domains)


def _extract_needs(need_answer: str) -> tuple[str, ...]:
    lowered = need_answer.lower()
    needs: list[str] = []
    if _contains_any(lowered, ("self-compassion", "самоспівчуття", "self compassion")):
        needs.append("self_compassion")
    if _contains_any(
        lowered,
        ("emotional tolerance", "емоційна толерантність", "tolerancia emocional"),
    ):
        needs.append("emotional_tolerance")
    if _contains_any(lowered, ("stabilization", "стабілізація", "estabilización")):
        needs.append("stabilization")
    return tuple(needs)


def build_profile_from_answers(answers: GuidedAssessmentAnswers) -> GuidedProfileResult:
    """Map guided intake answers to a demo PersonFitProfile."""
    corpus = combined_answer_text(answers)
    active_signals: list[str] = []
    risk_signals: list[str] = []

    if _contains_any(corpus, SHAME_KEYWORDS):
        active_signals.append("shame_sensitivity")
    if _contains_any(corpus, CRITIC_KEYWORDS):
        active_signals.append("harsh_self_criticism")
    if _contains_any(corpus, AVOID_KEYWORDS):
        active_signals.append("emotional_avoidance")
    if _contains_any(corpus, OVERWHELM_KEYWORDS):
        active_signals.append("overwhelm_risk")
        risk_signals.append("overwhelm_risk")

    needs = _extract_needs(answers.q_need)
    active_tuple = tuple(dict.fromkeys(active_signals))
    risk_tuple = tuple(dict.fromkeys(risk_signals))

    if not active_tuple:
        return GuidedProfileResult(
            profile=None,
            insufficient_coverage=True,
            active_signals=(),
            needs=needs,
        )

    profile = PersonFitProfile(
        profile_id="guided_assessment_profile",
        active_signals=active_tuple,
        dominant_domains=_infer_dominant_domains(active_tuple),
        risk_signals=risk_tuple,
        needs=needs,
        session_phase="preparation",
    )
    return GuidedProfileResult(
        profile=profile,
        insufficient_coverage=False,
        active_signals=active_tuple,
        needs=needs,
    )
