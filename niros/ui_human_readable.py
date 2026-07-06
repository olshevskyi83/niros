"""Human-readable labels and copy for the NIROS Streamlit workstation."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import PersonFitProfile, PatternFitScore
from niros.strategy_candidate_builder import StrategyCandidate

LANG_EN = "en"
LANG_ES = "es"
LANG_UK = "uk"

SUPPORTED_LANGUAGES: tuple[str, ...] = (LANG_EN, LANG_ES, LANG_UK)

UI_LANGUAGE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("English", LANG_EN),
    ("Español", LANG_ES),
    ("Українська", LANG_UK),
)

_SHAME_PROFILE_SIGNALS = frozenset(
    {"shame_sensitivity", "harsh_self_criticism", "emotional_avoidance"}
)

SIGNAL_LABELS: dict[str, dict[str, str]] = {
    "shame_sensitivity": {
        LANG_EN: "Shame sensitivity",
        LANG_ES: "Sensibilidad a la vergüenza",
        LANG_UK: "Чутливість до сорому",
    },
    "harsh_self_criticism": {
        LANG_EN: "Harsh self-criticism",
        LANG_ES: "Autocrítica severa",
        LANG_UK: "Жорстка самокритика",
    },
    "emotional_avoidance": {
        LANG_EN: "Emotional avoidance",
        LANG_ES: "Evitación emocional",
        LANG_UK: "Уникання емоцій",
    },
    "overwhelm_risk": {
        LANG_EN: "Overwhelm risk",
        LANG_ES: "Riesgo de agobio",
        LANG_UK: "Ризик перевантаження",
    },
    "self_compassion": {
        LANG_EN: "Self-compassion",
        LANG_ES: "Autocompasión",
        LANG_UK: "Самоспівчуття",
    },
    "emotional_tolerance": {
        LANG_EN: "Emotional tolerance",
        LANG_ES: "Tolerancia emocional",
        LANG_UK: "Емоційна толерантність",
    },
}

DOMAIN_LABELS: dict[str, dict[str, str]] = {
    "self": {
        LANG_EN: "Self",
        LANG_ES: "Yo",
        LANG_UK: "Я",
    },
    "emotion_regulation": {
        LANG_EN: "Emotion regulation",
        LANG_ES: "Regulación emocional",
        LANG_UK: "Регуляція емоцій",
    },
    "values": {
        LANG_EN: "Values",
        LANG_ES: "Valores",
        LANG_UK: "Цінності",
    },
    "meaning": {
        LANG_EN: "Meaning",
        LANG_ES: "Significado",
        LANG_UK: "Сенс",
    },
    "cognitive": {
        LANG_EN: "Cognitive",
        LANG_ES: "Cognitivo",
        LANG_UK: "Когнітивна сфера",
    },
}

PATTERN_NAME_LABELS: dict[str, dict[str, str]] = {
    "self compassion for shame": {
        LANG_EN: "Self-compassion for shame",
        LANG_ES: "Autocompasión ante la vergüenza",
        LANG_UK: "Самоспівчуття до сорому",
    },
    "acceptance of difficult emotions": {
        LANG_EN: "Acceptance of difficult emotions",
        LANG_ES: "Aceptación de emociones difíciles",
        LANG_UK: "Прийняття складних емоцій",
    },
    "deep emotional exposure": {
        LANG_EN: "Deep emotional exposure",
        LANG_ES: "Exposición emocional profunda",
        LANG_UK: "Глибока емоційна експозиція",
    },
    "stabilization before deep work": {
        LANG_EN: "Stabilization before deep work",
        LANG_ES: "Estabilización antes del trabajo profundo",
        LANG_UK: "Стабілізація перед глибокою роботою",
    },
}

SESSION_SUMMARY_TEMPLATES: dict[str, dict[str, str]] = {
    "shame_profile": {
        LANG_EN: (
            "NIROS detected a profile dominated by shame, self-criticism, and emotional "
            "avoidance. The recommended strategy prioritizes self-compassion and acceptance "
            "before any deeper emotional exposure."
        ),
        LANG_ES: (
            "NIROS detectó un perfil dominado por vergüenza, autocrítica y evitación "
            "emocional. La estrategia recomendada prioriza autocompasión y aceptación "
            "antes de cualquier exposición emocional profunda."
        ),
        LANG_UK: (
            "NIROS виявив профіль, у якому домінують сором, самокритика та уникання "
            "емоцій. Рекомендована стратегія спочатку ставить самоспівчуття й прийняття, "
            "а не глибоку емоційну експозицію."
        ),
    },
    "generic": {
        LANG_EN: (
            "NIROS analyzed the session and identified a personal profile with "
            "{signal_count} main signals. The recommended strategy focuses on the "
            "best-matching therapeutic patterns for this moment."
        ),
        LANG_ES: (
            "NIROS analizó la sesión e identificó un perfil personal con "
            "{signal_count} señales principales. La estrategia recomendada se centra "
            "en los patrones terapéuticos que mejor encajan en este momento."
        ),
        LANG_UK: (
            "NIROS проаналізував сесію й виявив особистий профіль із "
            "{signal_count} основними сигналами. Рекомендована стратегія зосереджена "
            "на терапевтичних патернах, які найкраще підходять зараз."
        ),
    },
}

CAUTION_REASON_TEMPLATES: dict[str, dict[str, str]] = {
    "deep emotional exposure": {
        LANG_EN: (
            "It may be useful later, but current overwhelm risk suggests starting "
            "with stabilization or gentler work."
        ),
        LANG_ES: (
            "Puede ser útil más adelante, pero el riesgo actual de agobio sugiere "
            "empezar con estabilización o un trabajo más suave."
        ),
        LANG_UK: (
            "Це може бути корисним пізніше, але поточний ризик перевантаження "
            "підказує почати зі стабілізації або м’якшої роботи."
        ),
    },
    "generic": {
        LANG_EN: "Use with caution based on current risks and readiness.",
        LANG_ES: "Usar con precaución según los riesgos y la preparación actuales.",
        LANG_UK: "Застосовувати обережно з урахуванням поточних ризиків і готовності.",
    },
}

UI_STRINGS: dict[str, dict[str, str]] = {
    "subtitle": {
        LANG_EN: "Human Digital Fingerprint Workstation",
        LANG_ES: "Estación de trabajo de huella digital humana",
        LANG_UK: "Робоча станція Human Digital Fingerprint",
    },
    "interface_language": {
        LANG_EN: "Interface language",
        LANG_ES: "Idioma de la interfaz",
        LANG_UK: "Мова інтерфейсу",
    },
    "patient_session": {
        LANG_EN: "Patient / Session",
        LANG_ES: "Paciente / Sesión",
        LANG_UK: "Пацієнт / Сесія",
    },
    "repository_status": {
        LANG_EN: "Repository status",
        LANG_ES: "Estado del repositorio",
        LANG_UK: "Стан репозиторію",
    },
    "patients_count": {
        LANG_EN: "Patients",
        LANG_ES: "Pacientes",
        LANG_UK: "Пацієнти",
    },
    "sessions_count": {
        LANG_EN: "Sessions",
        LANG_ES: "Sesiones",
        LANG_UK: "Сесії",
    },
    "create_patient": {
        LANG_EN: "Create patient",
        LANG_ES: "Crear paciente",
        LANG_UK: "Створити пацієнта",
    },
    "create_patient_first": {
        LANG_EN: "Create patient first.",
        LANG_ES: "Cree un paciente primero.",
        LANG_UK: "Спочатку створіть пацієнта.",
    },
    "select_patient": {
        LANG_EN: "Select patient",
        LANG_ES: "Seleccionar paciente",
        LANG_UK: "Обрати пацієнта",
    },
    "patient_notes": {
        LANG_EN: "Patient notes (optional, for new patient)",
        LANG_ES: "Notas del paciente (opcional, para paciente nuevo)",
        LANG_UK: "Нотатки пацієнта (необов’язково, для нового пацієнта)",
    },
    "patient_notes_placeholder": {
        LANG_EN: "Anonymous notes only — no names required",
        LANG_ES: "Solo notas anónimas — no se requieren nombres",
        LANG_UK: "Лише анонімні нотатки — імена не потрібні",
    },
    "no_sessions_yet": {
        LANG_EN: "No sessions yet.",
        LANG_ES: "Aún no hay sesiones.",
        LANG_UK: "Сесій ще немає.",
    },
    "input": {
        LANG_EN: "Input",
        LANG_ES: "Entrada",
        LANG_UK: "Введення",
    },
    "input_mode": {
        LANG_EN: "Input mode",
        LANG_ES: "Modo de entrada",
        LANG_UK: "Режим введення",
    },
    "mode_text": {
        LANG_EN: "Text",
        LANG_ES: "Texto",
        LANG_UK: "Текст",
    },
    "mode_voice_mock": {
        LANG_EN: "Voice Transcript Mock",
        LANG_ES: "Transcripción de voz simulada",
        LANG_UK: "Імітація голосової транскрипції",
    },
    "input_placeholder": {
        LANG_EN: "Describe what is happening for you right now...",
        LANG_ES: "Describe lo que te está pasando ahora...",
        LANG_UK: "Опишіть, що зараз відбувається з вами...",
    },
    "analyze_session": {
        LANG_EN: "Analyze Session",
        LANG_ES: "Analizar sesión",
        LANG_UK: "Аналізувати сесію",
    },
    "session_summary": {
        LANG_EN: "Session Summary",
        LANG_ES: "Resumen de la sesión",
        LANG_UK: "Підсумок сесії",
    },
    "fingerprint_title": {
        LANG_EN: "Human Digital Fingerprint",
        LANG_ES: "Huella digital humana",
        LANG_UK: "Human Digital Fingerprint",
    },
    "main_signals": {
        LANG_EN: "Main signals",
        LANG_ES: "Señales principales",
        LANG_UK: "Основні сигнали",
    },
    "main_domains": {
        LANG_EN: "Main domains",
        LANG_ES: "Dominios principales",
        LANG_UK: "Основні домени",
    },
    "current_risks": {
        LANG_EN: "Current risks",
        LANG_ES: "Riesgos actuales",
        LANG_UK: "Поточні ризики",
    },
    "current_needs": {
        LANG_EN: "Current needs",
        LANG_ES: "Necesidades actuales",
        LANG_UK: "Поточні потреби",
    },
    "recommended_strategy": {
        LANG_EN: "Recommended Strategy",
        LANG_ES: "Estrategia recomendada",
        LANG_UK: "Рекомендована стратегія",
    },
    "fit_label": {
        LANG_EN: "Fit",
        LANG_ES: "Ajuste",
        LANG_UK: "Відповідність",
    },
    "why_label": {
        LANG_EN: "Why",
        LANG_ES: "Por qué",
        LANG_UK: "Чому",
    },
    "caution_title": {
        LANG_EN: "Caution / Not now",
        LANG_ES: "Precaución / Ahora no",
        LANG_UK: "Обережно / Не зараз",
    },
    "use_with_caution": {
        LANG_EN: "Use with caution.",
        LANG_ES: "Usar con precaución.",
        LANG_UK: "Застосовувати обережно.",
    },
    "reason_label": {
        LANG_EN: "Reason",
        LANG_ES: "Motivo",
        LANG_UK: "Причина",
    },
    "excluded_count": {
        LANG_EN: "{count} patterns were not prioritized for this session.",
        LANG_ES: "{count} patrones no se priorizaron para esta sesión.",
        LANG_UK: "{count} патернів не було пріоритизовано для цієї сесії.",
    },
    "no_selected_patterns": {
        LANG_EN: "No patterns were selected for this session.",
        LANG_ES: "No se seleccionaron patrones para esta sesión.",
        LANG_UK: "Для цієї сесії не обрано патернів.",
    },
    "no_caution_patterns": {
        LANG_EN: "No caution patterns for this session.",
        LANG_ES: "No hay patrones de precaución para esta sesión.",
        LANG_UK: "Немає патернів обережності для цієї сесії.",
    },
    "advanced_details": {
        LANG_EN: "Advanced technical details",
        LANG_ES: "Detalles técnicos avanzados",
        LANG_UK: "Розширені технічні деталі",
    },
    "repository_admin": {
        LANG_EN: "Repository Admin",
        LANG_ES: "Administración del repositorio",
        LANG_UK: "Адміністрування репозиторію",
    },
    "enter_text_warning": {
        LANG_EN: "Please enter some text before analyzing.",
        LANG_ES: "Introduzca texto antes de analizar.",
        LANG_UK: "Введіть текст перед аналізом.",
    },
    "no_patient_warning": {
        LANG_EN: "No patient selected. Session was not saved.",
        LANG_ES: "No hay paciente seleccionado. La sesión no se guardó.",
        LANG_UK: "Пацієнта не обрано. Сесію не збережено.",
    },
    "session_saved": {
        LANG_EN: "Session saved",
        LANG_ES: "Sesión guardada",
        LANG_UK: "Сесію збережено",
    },
    "last_saved_session": {
        LANG_EN: "Last saved session",
        LANG_ES: "Última sesión guardada",
        LANG_UK: "Остання збережена сесія",
    },
    "run_analyze_hint": {
        LANG_EN: "Run Analyze Session to see results.",
        LANG_ES: "Pulse Analizar sesión para ver resultados.",
        LANG_UK: "Натисніть «Аналізувати сесію», щоб побачити результати.",
    },
    "created_patient": {
        LANG_EN: "Created",
        LANG_ES: "Creado",
        LANG_UK: "Створено",
    },
    "raw_explanation": {
        LANG_EN: "Raw explanation items",
        LANG_ES: "Elementos de explicación sin procesar",
        LANG_UK: "Сирі елементи пояснення",
    },
    "excluded_patterns": {
        LANG_EN: "Excluded patterns",
        LANG_ES: "Patrones excluidos",
        LANG_UK: "Виключені патерни",
    },
    "strategy_metadata": {
        LANG_EN: "Strategy metadata",
        LANG_ES: "Metadatos de estrategia",
        LANG_UK: "Метадані стратегії",
    },
}


def normalize_language(language: str) -> str:
    """Return a supported language code, defaulting to English."""
    if language in SUPPORTED_LANGUAGES:
        return language
    return LANG_EN


def ui_text(key: str, language: str, **kwargs: object) -> str:
    """Return a localized UI string."""
    lang = normalize_language(language)
    template = UI_STRINGS.get(key, {}).get(lang) or UI_STRINGS.get(key, {}).get(LANG_EN, key)
    if kwargs:
        return template.format(**kwargs)
    return template


def humanize_signal(signal: str, language: str) -> str:
    """Return a human-readable label for a profile signal."""
    lang = normalize_language(language)
    labels = SIGNAL_LABELS.get(signal, {})
    if lang in labels:
        return labels[lang]
    if LANG_EN in labels:
        return labels[LANG_EN]
    return signal.replace("_", " ").title()


def humanize_domain(domain: str, language: str) -> str:
    """Return a human-readable label for a profile domain."""
    lang = normalize_language(language)
    labels = DOMAIN_LABELS.get(domain, {})
    if lang in labels:
        return labels[lang]
    if LANG_EN in labels:
        return labels[LANG_EN]
    return domain.replace("_", " ").title()


def humanize_pattern_name(name: str, language: str) -> str:
    """Return a human-readable therapeutic pattern title."""
    lang = normalize_language(language)
    key = name.strip().lower()
    labels = PATTERN_NAME_LABELS.get(key, {})
    if lang in labels:
        return labels[lang]
    if LANG_EN in labels:
        return labels[LANG_EN]
    return name.strip().title()


def format_fit_percentage(fit_score: float) -> str:
    """Format a fit score as a whole-number percentage."""
    return f"{round(fit_score * 100)}%"


def _is_shame_demo_profile(profile: PersonFitProfile) -> bool:
    active = set(profile.active_signals)
    return _SHAME_PROFILE_SIGNALS.issubset(active)


def build_human_session_summary(
    profile: PersonFitProfile,
    strategy: StrategyCandidate,
    language: str,
) -> str:
    """Build a plain-language session summary from profile and strategy."""
    lang = normalize_language(language)
    _ = strategy  # strategy reserved for future template variants
    if _is_shame_demo_profile(profile):
        return SESSION_SUMMARY_TEMPLATES["shame_profile"][lang]
    template = SESSION_SUMMARY_TEMPLATES["generic"][lang]
    return template.format(signal_count=len(profile.active_signals))


def _join_readable(items: tuple[str, ...], language: str, *, humanizer) -> str:
    labels = [humanizer(item, language) for item in items]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        if language == LANG_EN:
            return f"{labels[0]} and {labels[1]}"
        if language == LANG_ES:
            return f"{labels[0]} y {labels[1]}"
        return f"{labels[0]} та {labels[1]}"
    if language == LANG_EN:
        return ", ".join(labels[:-1]) + f", and {labels[-1]}"
    if language == LANG_ES:
        return ", ".join(labels[:-1]) + f" y {labels[-1]}"
    return ", ".join(labels[:-1]) + f" та {labels[-1]}"


def build_human_pattern_reason(score: PatternFitScore, language: str) -> str:
    """Build a short plain-language reason for a recommended pattern."""
    lang = normalize_language(language)
    pattern_key = score.canonical_name.strip().lower()

    if pattern_key == "self compassion for shame":
        if lang == LANG_ES:
            return "Coincide con sensibilidad a la vergüenza y autocrítica severa."
        if lang == LANG_UK:
            return "Відповідає чутливості до сорому та жорсткій самокритиці."
        return "Matches shame sensitivity and harsh self-criticism."

    if pattern_key == "acceptance of difficult emotions":
        if lang == LANG_ES:
            return "Coincide con evitación emocional y la necesidad de tolerancia emocional."
        if lang == LANG_UK:
            return "Відповідає униканню емоцій і потребі в емоційній толерантності."
        return "Matches emotional avoidance and the need for emotional tolerance."

    signals_text = _join_readable(score.matched_signals, lang, humanizer=humanize_signal)
    needs_text = _join_readable(score.matched_needs, lang, humanizer=humanize_signal)

    if signals_text and needs_text:
        if lang == LANG_ES:
            return f"Coincide con {signals_text} y la necesidad de {needs_text}."
        if lang == LANG_UK:
            return f"Відповідає {signals_text} і потребі в {needs_text}."
        return f"Matches {signals_text} and the need for {needs_text}."
    if signals_text:
        if lang == LANG_ES:
            return f"Coincide con {signals_text}."
        if lang == LANG_UK:
            return f"Відповідає {signals_text}."
        return f"Matches {signals_text}."
    if needs_text:
        if lang == LANG_ES:
            return f"Responde a la necesidad de {needs_text}."
        if lang == LANG_UK:
            return f"Відповідає потребі в {needs_text}."
        return f"Addresses the need for {needs_text}."
    return score.reason or ui_text("why_label", lang)


def build_human_caution_reason(score: PatternFitScore, language: str) -> str:
    """Build a plain-language caution reason for a pattern."""
    lang = normalize_language(language)
    pattern_key = score.canonical_name.strip().lower()
    templates = CAUTION_REASON_TEMPLATES.get(pattern_key) or CAUTION_REASON_TEMPLATES["generic"]
    return templates[lang]


def build_excluded_count_message(count: int, language: str) -> str:
    """Return a short message about excluded patterns."""
    return ui_text("excluded_count", language, count=count)
