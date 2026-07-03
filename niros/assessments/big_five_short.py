from __future__ import annotations

from niros.assessment import (
    AssessmentItem,
    AssessmentResponse,
    AssessmentResult,
    score_assessment,
)

BIG_FIVE_SHORT_RESULTS_TITLE = "=== NIROS Big Five Short Assessment ==="
EMPTY_BIG_FIVE_SHORT_RESULTS_TEXT = (
    f"{BIG_FIVE_SHORT_RESULTS_TITLE}\n\n"
    "No Big Five short assessment results are available yet."
)

SUPPORTED_LANGUAGES = frozenset({"en", "uk", "ru", "es"})
BIG_FIVE_TRAITS: tuple[str, ...] = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
)
SCALE_MIN = 1
SCALE_MAX = 5
FINGERPRINT_DIMENSION = "big_five"

BIG_FIVE_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "bf_o_01",
        "domain_id": "openness",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I enjoy exploring new ideas.",
            "uk": "Мені цікаво досліджувати нові ідеї.",
            "ru": "Мне нравится исследовать новые идеи.",
            "es": "Disfruto explorar ideas nuevas.",
        },
    },
    {
        "id": "bf_o_02",
        "domain_id": "openness",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I like trying unfamiliar activities.",
            "uk": "Мені подобається пробувати незнайомі заняття.",
            "ru": "Мне нравится пробовать незнакомые занятия.",
            "es": "Me gusta probar actividades poco familiares.",
        },
    },
    {
        "id": "bf_o_03",
        "domain_id": "openness",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I prefer routines and familiar approaches.",
            "uk": "Я надаю перевагу звичним підходам і рутині.",
            "ru": "Я предпочитаю привычные подходы и рутину.",
            "es": "Prefiero rutinas y enfoques familiares.",
        },
    },
    {
        "id": "bf_o_04",
        "domain_id": "openness",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I am not very interested in abstract concepts.",
            "uk": "Мене не дуже цікавлять абстрактні поняття.",
            "ru": "Меня не очень интересуют абстрактные понятия.",
            "es": "No me interesan mucho los conceptos abstractos.",
        },
    },
    {
        "id": "bf_c_01",
        "domain_id": "conscientiousness",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I follow through on plans I make.",
            "uk": "Я доводжу до кінця плани, які складаю.",
            "ru": "Я довожу до конца планы, которые составляю.",
            "es": "Cumplo los planes que hago.",
        },
    },
    {
        "id": "bf_c_02",
        "domain_id": "conscientiousness",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I keep my belongings and tasks organized.",
            "uk": "Я тримаю речі та справи в порядку.",
            "ru": "Я держу вещи и дела в порядке.",
            "es": "Mantengo mis cosas y tareas organizadas.",
        },
    },
    {
        "id": "bf_c_03",
        "domain_id": "conscientiousness",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I often leave tasks until the last minute.",
            "uk": "Я часто відкладаю справи до останньої хвилини.",
            "ru": "Я часто откладываю дела до последней минуты.",
            "es": "A menudo dejo las tareas para el último momento.",
        },
    },
    {
        "id": "bf_c_04",
        "domain_id": "conscientiousness",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I find it hard to stick to schedules.",
            "uk": "Мені важко дотримуватися розкладу.",
            "ru": "Мне трудно придерживаться расписания.",
            "es": "Me cuesta seguir horarios.",
        },
    },
    {
        "id": "bf_e_01",
        "domain_id": "extraversion",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I feel energized around other people.",
            "uk": "Поруч з іншими людьми я відчуваю прилив енергії.",
            "ru": "Рядом с другими людьми я чувствую прилив энергии.",
            "es": "Me siento con energía cuando estoy con otras personas.",
        },
    },
    {
        "id": "bf_e_02",
        "domain_id": "extraversion",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I speak up easily in groups.",
            "uk": "Мені легко висловлюватися в групі.",
            "ru": "Мне легко высказываться в группе.",
            "es": "Me resulta fácil hablar en grupo.",
        },
    },
    {
        "id": "bf_e_03",
        "domain_id": "extraversion",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I prefer quiet time alone to social events.",
            "uk": "Я надаю перевагу тихому часу наодинці, а не подіям.",
            "ru": "Я предпочитаю тихое время наедине, а не мероприятия.",
            "es": "Prefiero tiempo tranquilo a solas antes que eventos sociales.",
        },
    },
    {
        "id": "bf_e_04",
        "domain_id": "extraversion",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I rarely seek out lively company.",
            "uk": "Я рідко шукаю активне спілкування.",
            "ru": "Я редко ищу оживлённую компанию.",
            "es": "Rara vez busco compañía animada.",
        },
    },
    {
        "id": "bf_a_01",
        "domain_id": "agreeableness",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I try to be considerate of others' feelings.",
            "uk": "Я намагаюся враховувати почуття інших.",
            "ru": "Я стараюсь учитывать чувства других.",
            "es": "Intento ser considerado con los sentimientos de los demás.",
        },
    },
    {
        "id": "bf_a_02",
        "domain_id": "agreeableness",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I prefer cooperation over competition.",
            "uk": "Я надаю перевагу співпраці, а не змаганню.",
            "ru": "Я предпочитаю сотрудничество, а не соперничество.",
            "es": "Prefiero la cooperación a la competición.",
        },
    },
    {
        "id": "bf_a_03",
        "domain_id": "agreeableness",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I can be blunt even when it may hurt feelings.",
            "uk": "Я можу бути прямим, навіть якщо це може зачепити почуття.",
            "ru": "Я могу быть прямым, даже если это может задеть чувства.",
            "es": "Puedo ser directo incluso cuando eso puede herir sentimientos.",
        },
    },
    {
        "id": "bf_a_04",
        "domain_id": "agreeableness",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I find it hard to trust people at first.",
            "uk": "Мені спочатку важко довіряти людям.",
            "ru": "Мне сначала трудно доверять людям.",
            "es": "Me cuesta confiar en las personas al principio.",
        },
    },
    {
        "id": "bf_n_01",
        "domain_id": "neuroticism",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I worry about things that might go wrong.",
            "uk": "Я хвилююся про те, що може піти не так.",
            "ru": "Я беспокоюсь о том, что может пойти не так.",
            "es": "Me preocupa lo que podría salir mal.",
        },
    },
    {
        "id": "bf_n_02",
        "domain_id": "neuroticism",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I get stressed easily when things change.",
            "uk": "Я легко напружуюсь, коли все змінюється.",
            "ru": "Я легко напрягаюсь, когда всё меняется.",
            "es": "Me estreso con facilidad cuando las cosas cambian.",
        },
    },
    {
        "id": "bf_n_03",
        "domain_id": "neuroticism",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I stay calm under pressure.",
            "uk": "Я зберігаю спокій під тиском.",
            "ru": "Я сохраняю спокойствие под давлением.",
            "es": "Me mantengo calmado bajo presión.",
        },
    },
    {
        "id": "bf_n_04",
        "domain_id": "neuroticism",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I rarely feel anxious or upset.",
            "uk": "Я рідко відчуваю тривогу чи напруження.",
            "ru": "Я редко чувствую тревогу или напряжение.",
            "es": "Rara vez me siento ansioso o alterado.",
        },
    },
)

FORBIDDEN_ITEM_PHRASES: tuple[str, ...] = (
    " diagnosis",
    "diagnose ",
    "disorder",
    "clinical",
    "patholog",
    "depressed",
    "depression",
)


def get_big_five_short_items(language: str = "en") -> list[AssessmentItem]:
    _ = language if language in SUPPORTED_LANGUAGES else "en"
    return [
        AssessmentItem(
            id=str(spec["id"]),
            text_by_language=dict(spec["text_by_language"]),  # type: ignore[arg-type]
            domain_id=str(spec["domain_id"]),
            scale_min=SCALE_MIN,
            scale_max=SCALE_MAX,
            reverse_scored=bool(spec["reverse_scored"]),
            fingerprint_dimension=FINGERPRINT_DIMENSION,
        )
        for spec in BIG_FIVE_SHORT_ITEM_SPECS
    ]


def score_big_five_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_assessment(get_big_five_short_items(), responses)


def render_big_five_short_results(results: list[AssessmentResult]) -> str:
    if not results:
        return EMPTY_BIG_FIVE_SHORT_RESULTS_TEXT

    trait_order = {trait: index for index, trait in enumerate(BIG_FIVE_TRAITS)}
    ordered_results = sorted(
        results,
        key=lambda result: trait_order.get(result.domain_id, len(BIG_FIVE_TRAITS)),
    )

    lines = [BIG_FIVE_SHORT_RESULTS_TITLE, ""]
    for result in ordered_results:
        lines.extend(
            [
                f"Trait: {result.domain_id}",
                f"Score: {result.score:.2f}",
                f"Level: {result.interpretation}",
                f"Fingerprint dimension: {result.fingerprint_dimension}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def item_text_for_language(item: AssessmentItem, language: str) -> str:
    lang = language if language in SUPPORTED_LANGUAGES else "en"
    return item.text_by_language.get(lang, item.text_by_language["en"])


def big_five_short_item_has_neutral_wording(item: AssessmentItem) -> bool:
    for text in item.text_by_language.values():
        lowered = text.lower()
        if any(phrase in lowered for phrase in FORBIDDEN_ITEM_PHRASES):
            return False
    return True
