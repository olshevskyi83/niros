from __future__ import annotations

from dataclasses import dataclass, field

SUPPORTED_INTAKE_LANGUAGES = frozenset({"en", "uk", "ru", "es"})

PRESENTING_PROBLEM_ID = "presenting_problem"
DURATION_ID = "duration"
PERCEIVED_CAUSES_ID = "perceived_causes"
CURRENT_IMPACT_ID = "current_impact"
PREVIOUS_ATTEMPTS_ID = "previous_attempts"
DESIRED_OUTCOME_ID = "desired_outcome"

INTAKE_QUESTION_ORDER: tuple[str, ...] = (
    PRESENTING_PROBLEM_ID,
    DURATION_ID,
    PERCEIVED_CAUSES_ID,
    CURRENT_IMPACT_ID,
    PREVIOUS_ATTEMPTS_ID,
    DESIRED_OUTCOME_ID,
)


@dataclass(frozen=True)
class IntakeQuestion:
    id: str
    text_by_language: dict[str, str]
    purpose: str
    expected_signal_types: tuple[str, ...]


@dataclass
class IntakeState:
    answers_by_question_id: dict[str, str] = field(default_factory=dict)
    completed: bool = False
    language: str = "en"


@dataclass(frozen=True)
class IntakeProtocol:
    questions: tuple[IntakeQuestion, ...]

    def question_ids(self) -> tuple[str, ...]:
        return tuple(question.id for question in self.questions)

    def get_question(self, question_id: str) -> IntakeQuestion:
        for question in self.questions:
            if question.id == question_id:
                return question
        raise KeyError(f"Unknown intake question id: {question_id}")

    def question_text(self, question_id: str, language: str) -> str:
        question = self.get_question(question_id)
        normalized_language = language if language in SUPPORTED_INTAKE_LANGUAGES else "en"
        return question.text_by_language.get(
            normalized_language,
            question.text_by_language["en"],
        )

    def all_question_texts(self, language: str) -> list[str]:
        return [self.question_text(question_id, language) for question_id in self.question_ids()]


DEFAULT_INTAKE_PROTOCOL = IntakeProtocol(
    questions=(
        IntakeQuestion(
            id=PRESENTING_PROBLEM_ID,
            text_by_language={
                "uk": "З якою головною проблемою або запитом ви сьогодні прийшли?",
                "en": "What main problem or request brings you here today?",
                "ru": "С какой главной проблемой или запросом вы сегодня пришли?",
                "es": "¿Con qué problema o petición principal vienes hoy?",
            },
            purpose="Capture the person's self-reported presenting problem or request.",
            expected_signal_types=("presenting_problem", "emotional_signal", "safety_signal"),
        ),
        IntakeQuestion(
            id=DURATION_ID,
            text_by_language={
                "uk": "Як давно це триває?",
                "en": "How long has this been going on?",
                "ru": "Как давно это продолжается?",
                "es": "¿Desde cuándo ocurre esto?",
            },
            purpose="Capture self-reported duration without clinical timeline interpretation.",
            expected_signal_types=("duration", "chronicity"),
        ),
        IntakeQuestion(
            id=PERCEIVED_CAUSES_ID,
            text_by_language={
                "uk": "Як ви самі думаєте, що могло сприяти виникненню цієї проблеми?",
                "en": "What do you think may have contributed to this problem?",
                "ru": "Как вы сами думаете, что могло способствовать появлению этой проблемы?",
                "es": "¿Qué crees que pudo haber contribuido a este problema?",
            },
            purpose="Capture self-reported perceived contributors.",
            expected_signal_types=("perceived_causes", "stress_signal", "body_signal"),
        ),
        IntakeQuestion(
            id=CURRENT_IMPACT_ID,
            text_by_language={
                "uk": "Як ця проблема зараз найбільше впливає на ваше життя?",
                "en": "How is this problem affecting your life right now?",
                "ru": "Как эта проблема сейчас больше всего влияет на вашу жизнь?",
                "es": "¿Cómo está afectando este problema a tu vida ahora?",
            },
            purpose="Capture self-reported functional impact.",
            expected_signal_types=("current_impact", "sleep_signal", "function_impact"),
        ),
        IntakeQuestion(
            id=PREVIOUS_ATTEMPTS_ID,
            text_by_language={
                "uk": "Що ви вже пробували, щоб з цим впоратися, і що допомагало або не допомагало?",
                "en": "What have you already tried to deal with this, and what helped or did not help?",
                "ru": "Что вы уже пробовали, чтобы справиться с этим, и что помогало или не помогало?",
                "es": "¿Qué has intentado ya para manejar esto, y qué ayudó o no ayudó?",
            },
            purpose="Capture self-reported coping attempts and outcomes.",
            expected_signal_types=("previous_attempts", "treatment_history"),
        ),
        IntakeQuestion(
            id=DESIRED_OUTCOME_ID,
            text_by_language={
                "uk": "Який результат цієї роботи був би для вас справді корисним?",
                "en": "What outcome from this work would feel genuinely useful to you?",
                "ru": "Какой результат этой работы был бы для вас действительно полезным?",
                "es": "¿Qué resultado de este trabajo sería realmente útil para ti?",
            },
            purpose="Capture self-reported desired outcome from the work.",
            expected_signal_types=("desired_outcome", "meaning_seeking", "change_desire"),
        ),
    )
)


def build_presenting_problem(intake_state: IntakeState) -> dict[str, str]:
    answers = intake_state.answers_by_question_id
    return {
        "main_problem": answers.get(PRESENTING_PROBLEM_ID, ""),
        "duration": answers.get(DURATION_ID, ""),
        "perceived_causes": answers.get(PERCEIVED_CAUSES_ID, ""),
        "current_impact": answers.get(CURRENT_IMPACT_ID, ""),
        "previous_attempts": answers.get(PREVIOUS_ATTEMPTS_ID, ""),
        "desired_outcome": answers.get(DESIRED_OUTCOME_ID, ""),
    }


def intake_state_from_answers(
    answers_by_question_id: dict[str, str],
    *,
    language: str = "en",
) -> IntakeState:
    protocol = DEFAULT_INTAKE_PROTOCOL
    missing = [question_id for question_id in protocol.question_ids() if question_id not in answers_by_question_id]
    return IntakeState(
        answers_by_question_id=dict(answers_by_question_id),
        completed=not missing,
        language=language,
    )
