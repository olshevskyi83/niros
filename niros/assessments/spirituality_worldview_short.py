from __future__ import annotations

from niros.assessment import AssessmentResponse, AssessmentResult
from niros.assessments._common import get_items_from_specs, score_items
from niros.spirituality_worldview import SPIRITUALITY_WORLDVIEW_DOMAIN

SPIRITUALITY_WORLDVIEW_SHORT_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "id": "swv_01",
        "domain_id": "worldview_orientation_signal",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I can describe my worldview or spiritual orientation in my own words.",
            "uk": "Я можу описати своє світоглядне або духовне ставлення своїми словами.",
            "ru": "Я могу описать своё мировоззрение или духовную ориентацию своими словами.",
            "es": "Puedo describir mi cosmovisión u orientación espiritual con mis propias palabras.",
        },
    },
    {
        "id": "swv_02",
        "domain_id": "religious_language_avoidance",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Religious or God language feels uncomfortable or unhelpful for me.",
            "uk": "Релігійна або Божественна мова відчувається для мене незручною або непридатною.",
            "ru": "Религиозная или божественная речь ощущается для меня неудобной или неподходящей.",
            "es": "El lenguaje religioso o sobre Dios me resulta incómodo o poco útil.",
        },
    },
    {
        "id": "swv_03",
        "domain_id": "religious_language_preference",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Faith-based or explicitly spiritual language can feel meaningful when it fits me.",
            "uk": "Мова віри або явно духовна мова може бути змістовною, коли вона мені підходить.",
            "ru": "Язык веры или явно духовная речь могут быть значимыми, когда они мне подходят.",
            "es": "El lenguaje de fe o espiritual explícito puede sentirse significativo cuando encaja conmigo.",
        },
    },
    {
        "id": "swv_04",
        "domain_id": "symbolic_openness_signal",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Symbolic, poetic, or metaphorical language can move me even without literal belief.",
            "uk": "Символічна, поетична або метафорична мова може вразити мене навіть без буквальної віри.",
            "ru": "Символический, поэтический или метафорический язык может тронуть меня даже без буквальной веры.",
            "es": "El lenguaje simbólico, poético o metafórico puede conmoverme incluso sin creencia literal.",
        },
    },
    {
        "id": "swv_05",
        "domain_id": "nature_symbolic_preference",
        "reverse_scored": False,
        "text_by_language": {
            "en": "Nature imagery such as forests, rivers, light, or mountains resonates with me.",
            "uk": "Природні образи, як-от ліси, ріки, світло чи гори, резонують зі мною.",
            "ru": "Образы природы, такие как леса, реки, свет или горы, откликаются во мне.",
            "es": "Las imágenes de la naturaleza, como bosques, ríos, luz o montañas, resuenan conmigo.",
        },
    },
    {
        "id": "swv_06",
        "domain_id": "secular_framing_preference",
        "reverse_scored": False,
        "text_by_language": {
            "en": "I prefer secular or psychological language over religious framing.",
            "uk": "Я надаю перевагу світській або психологічній мові над релігійним формулюванням.",
            "ru": "Я предпочитаю светский или психологический язык религиозному формулированию.",
            "es": "Prefiero un lenguaje secular o psicológico por encima del encuadre religioso.",
        },
    },
    {
        "id": "swv_07",
        "domain_id": "symbolic_preference_consent_waiver",
        "reverse_scored": True,
        "text_by_language": {
            "en": "I do not need NIROS to check my symbolic or spiritual language preferences before using them.",
            "uk": "Мені не потрібно, щоб NIROS перевіряв мої символічні чи духовні мовні вподобання перед їх використанням.",
            "ru": "Мне не нужно, чтобы NIROS проверял мои символические или духовные языковые предпочтения перед их использованием.",
            "es": "No necesito que NIROS verifique mis preferencias de lenguaje simbólico o espiritual antes de usarlas.",
        },
    },
)


def get_spirituality_worldview_short_items(language: str = "en"):
    return get_items_from_specs(
        SPIRITUALITY_WORLDVIEW_SHORT_ITEM_SPECS,
        SPIRITUALITY_WORLDVIEW_DOMAIN,
        language,
    )


def score_spirituality_worldview_short(responses: list[AssessmentResponse]) -> list[AssessmentResult]:
    return score_items(get_spirituality_worldview_short_items(), responses)
