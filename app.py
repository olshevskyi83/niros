"""NIROS Workstation — Streamlit UI for manual pipeline and patient admin."""

from __future__ import annotations

import streamlit as st

from niros.guided_assessment import (
    ALL_ANSWER_KEYS,
    INITIAL_QUESTION_KEY,
    INPUT_MODE_GUIDED,
    QUESTION_KEYS,
    WORKSTATION_MODE_GUIDED,
    WORKSTATION_MODE_QUICK_DEMO,
    GuidedAssessmentAnswers,
    all_required_answers_collected,
    build_coverage_status,
    build_profile_from_answers,
    build_transcript,
    insufficient_coverage_message,
    question_text,
    workstation_ui_text,
)
from niros.patient_repository import (
    DEFAULT_REPOSITORY_PATH,
    create_patient,
    create_session,
    list_sessions_for_patient,
    load_repository,
    save_repository,
)
from niros.ui_demo import (
    MODE_TEXT,
    MODE_VOICE_TRANSCRIPT_MOCK,
    NirosDemoResult,
    explanation_to_snapshot,
    input_mode_to_repository_value,
    profile_to_snapshot,
    run_niros_demo_pipeline,
    run_niros_pipeline_from_profile,
    strategy_to_snapshot,
)
from niros.ui_human_readable import (
    LANG_EN,
    UI_LANGUAGE_OPTIONS,
    build_excluded_count_message,
    build_human_caution_reason,
    build_human_pattern_reason,
    build_human_session_summary,
    format_fit_percentage,
    humanize_domain,
    humanize_pattern_name,
    humanize_signal,
    normalize_language,
    ui_text,
)

st.set_page_config(
    page_title="NIROS Workstation",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp {
            background-color: #121212;
            color: #e8e8e8;
        }
        .block-container {
            padding-top: 1.5rem;
            max-width: 1200px;
        }
        h1, h2, h3, h4, label, p, span, div {
            color: #e8e8e8;
        }
        .niros-subtitle {
            color: #9a9a9a;
            margin-bottom: 1rem;
        }
        .status-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .status-badge {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid transparent;
        }
        .status-active {
            background-color: #1b3d2a;
            color: #7dcea0;
            border-color: #2e6b45;
        }
        .status-mock {
            background-color: #4a3a12;
            color: #f0c674;
            border-color: #7a5a1a;
        }
        .status-off {
            background-color: #2a2a2a;
            color: #9a9a9a;
            border-color: #444444;
        }
        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin-bottom: 0.5rem;
        }
        .chip {
            display: inline-block;
            background-color: #1f1f1f;
            border: 1px solid #333333;
            border-radius: 999px;
            padding: 0.15rem 0.55rem;
            font-size: 0.8rem;
            color: #d8d8d8;
        }
        .panel-box {
            background-color: #181818;
            border: 1px solid #2d2d2d;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.85rem;
        }
        .panel-box h4 {
            margin: 0 0 0.5rem 0;
            font-size: 0.95rem;
            color: #c8c8c8;
        }
        .strategy-card {
            background-color: #181818;
            border: 1px solid #2d2d2d;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }
        .strategy-card h4 {
            margin: 0 0 0.35rem 0;
        }
        .strategy-card p {
            margin: 0.15rem 0;
            color: #c0c0c0;
            font-size: 0.92rem;
        }
        .summary-box {
            background-color: #1a2420;
            border: 1px solid #2e4a3a;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            line-height: 1.5;
        }
        .demo-warning {
            background-color: #3a2a10;
            border: 1px solid #7a5a1a;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin-bottom: 1rem;
            color: #f0c674;
            font-size: 0.92rem;
        }
        .coverage-item-done {
            color: #7dcea0;
            margin-bottom: 0.35rem;
        }
        .coverage-item-pending {
            color: #9a9a9a;
            margin-bottom: 0.35rem;
        }
        .guided-question {
            background-color: #181818;
            border: 1px solid #2d2d2d;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.85rem;
        }
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
            background-color: #1a1a1a;
            color: #e8e8e8;
            border: 1px solid #333333;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "repository" not in st.session_state:
    st.session_state.repository = load_repository()
if "selected_patient_id" not in st.session_state:
    st.session_state.selected_patient_id = None
if "last_saved_session_id" not in st.session_state:
    st.session_state.last_saved_session_id = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "ui_language" not in st.session_state:
    st.session_state.ui_language = LANG_EN
if "workstation_mode" not in st.session_state:
    st.session_state.workstation_mode = WORKSTATION_MODE_GUIDED
if "guided_answers" not in st.session_state:
    st.session_state.guided_answers = {key: "" for key in ALL_ANSWER_KEYS}
if "_prev_workstation_mode" not in st.session_state:
    st.session_state._prev_workstation_mode = st.session_state.workstation_mode


def _status_badges() -> None:
    badges = [
        ("Semantic Interpreter", "Mock", "status-mock"),
        ("Whisper", "Mock", "status-mock"),
        ("Patient Repository", "Active", "status-active"),
        ("TLE", "Active", "status-active"),
        ("Pattern–Person Fit", "Active", "status-active"),
        ("Sensors", "Not Connected", "status-off"),
        ("Icaro", "Not Connected", "status-off"),
    ]
    html = '<div class="status-row">'
    for label, state, css_class in badges:
        html += f'<span class="status-badge {css_class}">{label}: {state}</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _render_chip_group(title: str, values: tuple[str, ...], language: str, humanizer) -> None:
    if values:
        chips = "".join(
            f'<span class="chip">{humanizer(value, language)}</span>' for value in values
        )
        body = f'<div class="chip-row">{chips}</div>'
    else:
        body = "<p style='color:#888;margin:0;'>—</p>"
    st.markdown(
        f'<div class="panel-box"><h4>{title}</h4>{body}</div>',
        unsafe_allow_html=True,
    )


def _render_fingerprint(profile, language: str) -> None:
    st.subheader(ui_text("fingerprint_title", language))
    _render_chip_group(
        ui_text("main_signals", language),
        profile.active_signals,
        language,
        humanize_signal,
    )
    _render_chip_group(
        ui_text("main_domains", language),
        profile.dominant_domains,
        language,
        humanize_domain,
    )
    _render_chip_group(
        ui_text("current_risks", language),
        profile.risk_signals,
        language,
        humanize_signal,
    )
    _render_chip_group(
        ui_text("current_needs", language),
        profile.needs,
        language,
        humanize_signal,
    )


def _render_recommended_strategy(strategy, language: str) -> None:
    st.subheader(ui_text("recommended_strategy", language))
    if not strategy.selected_patterns:
        st.caption(ui_text("no_selected_patterns", language))
        return
    for score in strategy.selected_patterns:
        title = humanize_pattern_name(score.canonical_name, language)
        reason = build_human_pattern_reason(score, language)
        st.markdown(
            f"""
            <div class="strategy-card">
                <h4>{title}</h4>
                <p><strong>{ui_text("fit_label", language)}:</strong> {format_fit_percentage(score.fit_score)}</p>
                <p><strong>{ui_text("why_label", language)}:</strong> {reason}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    excluded_count = len(strategy.excluded_patterns)
    if excluded_count:
        st.caption(build_excluded_count_message(excluded_count, language))


def _render_caution(strategy, language: str) -> None:
    st.subheader(ui_text("caution_title", language))
    if not strategy.caution_patterns:
        st.caption(ui_text("no_caution_patterns", language))
        return
    for score in strategy.caution_patterns:
        title = humanize_pattern_name(score.canonical_name, language)
        reason = build_human_caution_reason(score, language)
        st.markdown(
            f"""
            <div class="strategy-card">
                <h4>{title}</h4>
                <p><strong>{ui_text("use_with_caution", language)}</strong></p>
                <p><strong>{ui_text("reason_label", language)}:</strong> {reason}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_advanced_details(result: NirosDemoResult, language: str) -> None:
    with st.expander(ui_text("advanced_details", language)):
        strategy = result.strategy
        explanation = result.explanation
        st.markdown(f"**{ui_text('strategy_metadata', language)}**")
        st.write(
            {
                "strategy_id": strategy.strategy_id,
                "profile_id": strategy.profile_id,
                "strategy_status": strategy.strategy_status,
                "selected": len(strategy.selected_patterns),
                "caution": len(strategy.caution_patterns),
                "excluded": len(strategy.excluded_patterns),
            }
        )
        st.markdown("**Selected patterns (raw)**")
        for score in strategy.selected_patterns:
            st.write(
                f"`{score.pattern_id}` · {score.canonical_name} · "
                f"fit={score.fit_score:.4f} · {score.recommendation_status}"
            )
        st.markdown("**Caution patterns (raw)**")
        for score in strategy.caution_patterns:
            st.write(
                f"`{score.pattern_id}` · {score.canonical_name} · "
                f"fit={score.fit_score:.4f} · {score.recommendation_status}"
            )
        st.markdown(f"**{ui_text('excluded_patterns', language)}**")
        if strategy.excluded_patterns:
            for score in strategy.excluded_patterns:
                st.write(
                    f"`{score.pattern_id}` · {score.canonical_name} · "
                    f"fit={score.fit_score:.4f} · {score.recommendation_status}"
                )
        else:
            st.caption("—")
        st.markdown(f"**{ui_text('raw_explanation', language)}**")
        st.write(explanation.summary)
        for item in explanation.explanation_items:
            st.write(f"- `{item.pattern_id}` — {item.canonical_name}: {item.explanation}")


def _render_session_summary_and_fingerprint(result: NirosDemoResult, language: str) -> None:
    st.subheader(ui_text("session_summary", language))
    summary = build_human_session_summary(result.profile, result.strategy, language)
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
    _render_fingerprint(result.profile, language)


def _render_coverage_status(answers: GuidedAssessmentAnswers, language: str) -> None:
    st.subheader(workstation_ui_text("coverage_status", language))
    for status in build_coverage_status(answers, language):
        css_class = "coverage-item-done" if status.collected else "coverage-item-pending"
        state_label = workstation_ui_text("collected" if status.collected else "pending", language)
        st.markdown(
            f'<p class="{css_class}">{"✓" if status.collected else "○"} '
            f'{status.label} · {state_label}</p>',
            unsafe_allow_html=True,
        )


def _save_session(
    *,
    transcript: str,
    input_mode: str,
    result: NirosDemoResult,
    language: str,
) -> None:
    if not st.session_state.selected_patient_id:
        st.warning(ui_text("no_patient_warning", language))
        return
    repository, session = create_session(
        st.session_state.repository,
        st.session_state.selected_patient_id,
        input_mode=input_mode,
        transcript=transcript,
        fingerprint_snapshot=profile_to_snapshot(result.profile),
        strategy_snapshot=strategy_to_snapshot(result.strategy),
        explanation_snapshot=explanation_to_snapshot(result.explanation),
    )
    save_repository(repository)
    st.session_state.repository = repository
    st.session_state.last_saved_session_id = session.session_id
    st.success(f"{ui_text('session_saved', language)}: `{session.session_id}`")


def _input_mode_options(language: str) -> list[tuple[str, str]]:
    return [
        (ui_text("mode_text", language), MODE_TEXT),
        (ui_text("mode_voice_mock", language), MODE_VOICE_TRANSCRIPT_MOCK),
    ]


def _render_quick_demo(left_col, right_col, language: str) -> None:
    st.markdown(
        f'<div class="demo-warning">{workstation_ui_text("demo_warning", language)}</div>',
        unsafe_allow_html=True,
    )
    mode_options = _input_mode_options(language)
    mode_value_by_label = {label: value for label, value in mode_options}

    with left_col:
        st.subheader(ui_text("input", language))
        selected_mode_label = st.radio(
            ui_text("input_mode", language),
            options=[label for label, _ in mode_options],
            horizontal=True,
            key="quick_demo_input_mode",
        )
        mode = mode_value_by_label[selected_mode_label]
        user_text = st.text_area(
            ui_text("input", language),
            placeholder=ui_text("input_placeholder", language),
            height=220,
            label_visibility="collapsed",
            key="quick_demo_text",
        )
        analyze = st.button(
            ui_text("analyze_session", language),
            type="primary",
            use_container_width=True,
            key="quick_demo_analyze",
        )

    strategy_placeholder = st.container()
    caution_placeholder = st.container()

    if analyze:
        if not user_text.strip():
            st.warning(ui_text("enter_text_warning", language))
            st.session_state.last_result = None
        else:
            result = run_niros_demo_pipeline(user_text, mode=mode)
            st.session_state.last_result = result
            transcript_text = (
                result.voice_transcript.transcript
                if result.voice_transcript is not None
                else result.input_text
            )
            _save_session(
                transcript=transcript_text,
                input_mode=input_mode_to_repository_value(mode),
                result=result,
                language=language,
            )

    result = st.session_state.last_result
    if result is not None:
        with right_col:
            _render_session_summary_and_fingerprint(result, language)
        with strategy_placeholder:
            _render_recommended_strategy(result.strategy, language)
        with caution_placeholder:
            _render_caution(result.strategy, language)
        _render_advanced_details(result, language)
    else:
        with right_col:
            st.caption(ui_text("run_analyze_hint", language))


def _render_guided_assessment(left_col, right_col, language: str) -> None:
    answers_dict = st.session_state.guided_answers

    with left_col:
        st.subheader(workstation_ui_text("guided_intake", language))
        st.markdown(f"**{workstation_ui_text('step_initial', language)}**")
        answers_dict[INITIAL_QUESTION_KEY] = st.text_area(
            question_text(INITIAL_QUESTION_KEY, language),
            value=answers_dict.get(INITIAL_QUESTION_KEY, ""),
            height=100,
            key="guided_initial",
        )

        st.markdown(f"**{workstation_ui_text('step_clarification', language)}**")
        for question_key in QUESTION_KEYS:
            answers_dict[question_key] = st.text_area(
                question_text(question_key, language),
                value=answers_dict.get(question_key, ""),
                height=90,
                key=f"guided_{question_key}",
            )

        answers = GuidedAssessmentAnswers.from_dict(answers_dict)
        st.session_state.guided_answers = answers.as_dict()
        ready = all_required_answers_collected(answers)

        if not ready:
            st.caption(workstation_ui_text("complete_all_questions", language))

        generate = st.button(
            workstation_ui_text("generate_fingerprint_strategy", language),
            type="primary",
            use_container_width=True,
            disabled=not ready,
            key="guided_generate",
        )

    strategy_placeholder = st.container()
    caution_placeholder = st.container()

    with right_col:
        if st.session_state.last_result is not None:
            _render_session_summary_and_fingerprint(st.session_state.last_result, language)
        else:
            _render_coverage_status(answers, language)

    if generate:
        profile_result = build_profile_from_answers(answers)
        if profile_result.insufficient_coverage:
            st.warning(insufficient_coverage_message(language))
            st.session_state.last_result = None
        else:
            assert profile_result.profile is not None
            transcript = build_transcript(answers, language)
            result = run_niros_pipeline_from_profile(
                profile_result.profile,
                input_text=transcript,
            )
            st.session_state.last_result = result
            _save_session(
                transcript=transcript,
                input_mode=INPUT_MODE_GUIDED,
                result=result,
                language=language,
            )
            st.rerun()

    result = st.session_state.last_result
    if result is not None and st.session_state.workstation_mode == WORKSTATION_MODE_GUIDED:
        with strategy_placeholder:
            _render_recommended_strategy(result.strategy, language)
        with caution_placeholder:
            _render_caution(result.strategy, language)
        _render_advanced_details(result, language)


repository = st.session_state.repository
sidebar = st.sidebar

language_labels = [label for label, _ in UI_LANGUAGE_OPTIONS]
language_codes = {label: code for label, code in UI_LANGUAGE_OPTIONS}
default_lang_index = next(
    (
        index
        for index, (_, code) in enumerate(UI_LANGUAGE_OPTIONS)
        if code == st.session_state.ui_language
    ),
    0,
)
selected_language_label = sidebar.selectbox(
    ui_text("interface_language", st.session_state.ui_language),
    options=language_labels,
    index=default_lang_index,
)
language = normalize_language(language_codes[selected_language_label])
st.session_state.ui_language = language

st.title("NIROS")
st.markdown(
    f'<p class="niros-subtitle">{ui_text("subtitle", language)}</p>',
    unsafe_allow_html=True,
)
_status_badges()

sidebar.header(ui_text("patient_session", language))
sidebar.markdown(f"**{ui_text('repository_status', language)}**")
sidebar.write(f"{ui_text('patients_count', language)}: {len(repository.patients)}")
sidebar.write(f"{ui_text('sessions_count', language)}: {len(repository.sessions)}")

new_patient_notes = sidebar.text_input(
    ui_text("patient_notes", language),
    placeholder=ui_text("patient_notes_placeholder", language),
)

if sidebar.button(ui_text("create_patient", language), use_container_width=True):
    repository, patient = create_patient(repository, notes=new_patient_notes.strip())
    save_repository(repository)
    st.session_state.repository = repository
    st.session_state.selected_patient_id = patient.patient_id
    st.session_state.last_saved_session_id = None
    sidebar.success(f"{ui_text('created_patient', language)} {patient.patient_id}")

patient_ids = [patient.patient_id for patient in repository.patients]
if patient_ids:
    default_index = 0
    if st.session_state.selected_patient_id in patient_ids:
        default_index = patient_ids.index(st.session_state.selected_patient_id)
    selected_patient_id = sidebar.selectbox(
        ui_text("select_patient", language),
        options=patient_ids,
        index=default_index,
    )
    st.session_state.selected_patient_id = selected_patient_id
    patient_sessions = list_sessions_for_patient(repository, selected_patient_id)
    sidebar.markdown("**Sessions**")
    if patient_sessions:
        for session in patient_sessions:
            sidebar.write(f"- `{session.session_id}`")
    else:
        sidebar.caption(ui_text("no_sessions_yet", language))
else:
    sidebar.caption(ui_text("create_patient_first", language))
    st.session_state.selected_patient_id = None

workstation_options = [
    (workstation_ui_text("guided_assessment", language), WORKSTATION_MODE_GUIDED),
    (workstation_ui_text("quick_demo", language), WORKSTATION_MODE_QUICK_DEMO),
]
workstation_value_by_label = {label: value for label, value in workstation_options}
default_workstation_index = (
    0
    if st.session_state.workstation_mode == WORKSTATION_MODE_GUIDED
    else 1
)

selected_workstation_label = st.radio(
    workstation_ui_text("workstation_mode", language),
    options=[label for label, _ in workstation_options],
    index=default_workstation_index,
    horizontal=True,
)
selected_workstation_mode = workstation_value_by_label[selected_workstation_label]
if selected_workstation_mode != st.session_state._prev_workstation_mode:
    st.session_state.last_result = None
st.session_state.workstation_mode = selected_workstation_mode
st.session_state._prev_workstation_mode = selected_workstation_mode

left_col, right_col = st.columns(2, gap="large")

if selected_workstation_mode == WORKSTATION_MODE_QUICK_DEMO:
    _render_quick_demo(left_col, right_col, language)
else:
    _render_guided_assessment(left_col, right_col, language)

if st.session_state.last_saved_session_id:
    st.caption(
        f"{ui_text('last_saved_session', language)}: "
        f"`{st.session_state.last_saved_session_id}`"
    )

with st.expander(ui_text("repository_admin", language)):
    st.write(f"Repository file: `{DEFAULT_REPOSITORY_PATH}`")
    if repository.patients:
        st.markdown("**Patients**")
        st.dataframe(
            [
                {
                    "patient_id": patient.patient_id,
                    "created_at": patient.created_at,
                    "status": patient.status,
                    "notes": patient.notes,
                }
                for patient in repository.patients
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No patients stored.")

    if repository.sessions:
        st.markdown("**Sessions**")
        st.dataframe(
            [
                {
                    "session_id": session.session_id,
                    "patient_id": session.patient_id,
                    "created_at": session.created_at,
                    "input_mode": session.input_mode,
                    "transcript_preview": session.transcript[:80],
                }
                for session in repository.sessions
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No sessions stored.")
