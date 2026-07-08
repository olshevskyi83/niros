"""NIROS Workstation — Streamlit UI for manual pipeline and patient admin."""

from __future__ import annotations

from time import perf_counter

import streamlit as st

from niros.guided_assessment import (
    ALL_ANSWER_KEYS,
    INITIAL_QUESTION_KEY,
    INPUT_MODE_GUIDED,
    QUESTION_KEYS,
    WORKSTATION_MODE_GUIDED,
    WORKSTATION_MODE_KNOWLEDGE_FACTORY,
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
from niros.ctpc_compiler import CTPCCompilationValidationError
from niros.human_review_workflow import HumanReviewError
from niros.knowledge_compiler import (
    CompileProgressEvent,
    KnowledgeCompiler,
    PROGRESS_COMPLETED,
    PROGRESS_CONSOLIDATED,
    PROGRESS_CONSOLIDATING,
    PROGRESS_FAILED,
    PROGRESS_SAVING_REVIEWS,
)
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
    is_compilable_knowledge_domain,
)
from niros.knowledge_workspace import DEFAULT_KNOWLEDGE_ROOT
from niros.runtime_config import OPENAI_KEY_ENV_VAR, OPENAI_SETUP_HINT, has_openai_api_key
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
    get_runtime_pattern_library_summary,
    lookup_pattern_source_type,
    pattern_source_type_label,
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
from niros.ui_knowledge_factory import (
    DEFAULT_UI_MAX_BATCH_CHARS,
    DEFAULT_MAX_BATCHES_UI_OPTION,
    DEFAULT_REVIEW_MODE_UI_OPTION,
    MAX_BATCHES_UI_OPTIONS,
    REVIEW_MODE_UI_OPTIONS,
    SCANNED_PDF_GUIDANCE,
    assign_review_domain_for_ui,
    approve_review_for_ui,
    base_extraction_for_review,
    build_edited_extraction,
    compile_progress_ui_summary,
    compile_summary_ui_funnel,
    archive_pending_reviews_for_ui,
    parse_review_mode_option,
    format_multiline_field,
    import_knowledge_source_for_ui,
    list_extraction_results_for_ui,
    list_knowledge_library_sources_for_ui,
    list_latest_ctpc_patterns,
    load_review_for_ui,
    load_review_record,
    parse_max_batches_option,
    parse_multiline_field,
    reject_review_for_ui,
    request_changes_for_ui,
    review_can_be_approved,
    review_is_actionable,
    summarize_workspace,
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
if "kf_workspace_root" not in st.session_state:
    st.session_state.kf_workspace_root = DEFAULT_KNOWLEDGE_ROOT
if "kf_last_import" not in st.session_state:
    st.session_state.kf_last_import = None
if "kf_selected_review_id" not in st.session_state:
    st.session_state.kf_selected_review_id = None
if "kf_message" not in st.session_state:
    st.session_state.kf_message = ""
if "kf_knowledge_domain" not in st.session_state:
    st.session_state.kf_knowledge_domain = KNOWLEDGE_DOMAIN_VOCAL_ICARO
if "kf_compile_summary" not in st.session_state:
    st.session_state.kf_compile_summary = None
if "kf_compile_ui_summary" not in st.session_state:
    st.session_state.kf_compile_ui_summary = None

_KF_DOMAIN_OPTIONS: tuple[tuple[str, str], ...] = (
    (KNOWLEDGE_DOMAIN_VOCAL_ICARO, "Vocal / Icaro"),
    (KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE, "Psychotherapy / TLE"),
)


def _status_badges() -> None:
    library_summary = get_runtime_pattern_library_summary()
    tle_state = f"TLE Patterns: {library_summary.tle_badge_label}"
    badges = [
        ("Semantic Interpreter", "Mock", "status-mock"),
        ("Whisper", "Mock", "status-mock"),
        ("Patient Repository", "Active", "status-active"),
        (tle_state, "", "status-active"),
        ("Pattern–Person Fit", "Active", "status-active"),
        ("Sensors", "Not Connected", "status-off"),
        ("Icaro", "Not Connected", "status-off"),
    ]
    html = '<div class="status-row">'
    for label, state, css_class in badges:
        if state:
            html += f'<span class="status-badge {css_class}">{label}: {state}</span>'
        else:
            html += f'<span class="status-badge {css_class}">{label}</span>'
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


def _render_recommended_strategy(result: NirosDemoResult, language: str) -> None:
    strategy = result.strategy
    st.subheader(ui_text("recommended_strategy", language))
    if not strategy.selected_patterns:
        st.caption(ui_text("no_selected_patterns", language))
        return
    for score in strategy.selected_patterns:
        title = humanize_pattern_name(score.canonical_name, language)
        reason = build_human_pattern_reason(score, language)
        source_type = lookup_pattern_source_type(result.pattern_library, score.pattern_id)
        source_label = pattern_source_type_label(source_type)
        st.markdown(
            f"""
            <div class="strategy-card">
                <h4>{title}</h4>
                <p><strong>Source:</strong> {source_label}</p>
                <p><strong>{ui_text("fit_label", language)}:</strong> {format_fit_percentage(score.fit_score)}</p>
                <p><strong>{ui_text("why_label", language)}:</strong> {reason}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    excluded_count = len(strategy.excluded_patterns)
    if excluded_count:
        st.caption(build_excluded_count_message(excluded_count, language))


def _render_caution(result: NirosDemoResult, language: str) -> None:
    strategy = result.strategy
    st.subheader(ui_text("caution_title", language))
    if not strategy.caution_patterns:
        st.caption(ui_text("no_caution_patterns", language))
        return
    for score in strategy.caution_patterns:
        title = humanize_pattern_name(score.canonical_name, language)
        reason = build_human_caution_reason(score, language)
        source_type = lookup_pattern_source_type(result.pattern_library, score.pattern_id)
        source_label = pattern_source_type_label(source_type)
        st.markdown(
            f"""
            <div class="strategy-card">
                <h4>{title}</h4>
                <p><strong>Source:</strong> {source_label}</p>
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
                "runtime_patterns_demo": result.library_summary.demo_count,
                "runtime_patterns_ctpc": result.library_summary.ctpc_count,
                "runtime_patterns_total": result.library_summary.total_count,
            }
        )
        st.markdown("**Selected patterns (raw)**")
        for score in strategy.selected_patterns:
            source_type = lookup_pattern_source_type(result.pattern_library, score.pattern_id)
            st.write(
                f"`{score.pattern_id}` · {score.canonical_name} · "
                f"source={source_type} · "
                f"fit={score.fit_score:.4f} · {score.recommendation_status}"
            )
        st.markdown("**Caution patterns (raw)**")
        for score in strategy.caution_patterns:
            source_type = lookup_pattern_source_type(result.pattern_library, score.pattern_id)
            st.write(
                f"`{score.pattern_id}` · {score.canonical_name} · "
                f"source={source_type} · "
                f"fit={score.fit_score:.4f} · {score.recommendation_status}"
            )
        st.markdown(f"**{ui_text('excluded_patterns', language)}**")
        if strategy.excluded_patterns:
            for score in strategy.excluded_patterns:
                source_type = lookup_pattern_source_type(result.pattern_library, score.pattern_id)
                st.write(
                    f"`{score.pattern_id}` · {score.canonical_name} · "
                    f"source={source_type} · "
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
            _render_recommended_strategy(result, language)
        with caution_placeholder:
            _render_caution(result, language)
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
            _render_recommended_strategy(result, language)
        with caution_placeholder:
            _render_caution(result, language)
        _render_advanced_details(result, language)


def _render_knowledge_factory(language: str) -> None:
    workspace_root = st.session_state.kf_workspace_root

    if st.session_state.kf_message:
        st.info(st.session_state.kf_message)

    st.subheader(workstation_ui_text("knowledge_factory", language))
    st.caption("Source → Extract → Consolidate → Review → CTPC")

    st.markdown(f"### {workstation_ui_text('kf_step_source', language)}")
    st.markdown(
        f'<div class="demo-warning">{SCANNED_PDF_GUIDANCE}</div>',
        unsafe_allow_html=True,
    )

    library_sources = list_knowledge_library_sources_for_ui()
    if st.button("Re-index Knowledge Library", key="kf_reindex_library"):
        library_sources = list_knowledge_library_sources_for_ui()
        st.session_state.kf_message = (
            f"Indexed {len(library_sources)} Knowledge Library sources."
        )
        st.rerun()
    if library_sources:
        count_rows = [
            {
                "domain": domain,
                "family": family,
                "source_type": source_type,
                "compile_status": compile_status,
                "sources": count,
            }
            for (domain, family, source_type, compile_status), count in sorted(
                {
                    (
                        source.domain,
                        source.family,
                        source.source_type,
                        source.compile_status,
                    ): sum(
                        1
                        for item in library_sources
                        if item.domain == source.domain
                        and item.family == source.family
                        and item.source_type == source.source_type
                        and item.compile_status == source.compile_status
                    )
                    for source in library_sources
                }.items()
            )
        ]
        st.dataframe(count_rows, use_container_width=True, hide_index=True)

    import_cols = st.columns([1, 1, 2, 1])
    selected_source = None
    with import_cols[0]:
        domain_options = sorted({source.domain for source in library_sources})
        if domain_options:
            selected_domain = st.selectbox(
                "Knowledge Library domain",
                options=domain_options,
                index=0,
                key="kf_library_domain_select",
            )
        else:
            selected_domain = None
            st.caption("No sources in knowledge_library yet.")
    with import_cols[1]:
        family_options = sorted(
            {
                source.family
                for source in library_sources
                if selected_domain and source.domain == selected_domain
            }
        )
        if family_options:
            selected_family = st.selectbox(
                "Family",
                options=family_options,
                index=0,
                key="kf_library_family_select",
            )
        else:
            selected_family = None
            st.caption("No family selected.")
    with import_cols[2]:
        source_options = [
            source
            for source in library_sources
            if selected_domain
            and selected_family
            and source.domain == selected_domain
            and source.family == selected_family
        ]
        source_labels = [
            f"{source.title} · {source.source_type} · {source.relative_path}"
            for source in source_options
        ]
        if source_labels:
            selected_source_label = st.selectbox(
                "Knowledge Library source",
                options=source_labels,
                index=0,
                key="kf_library_source_select",
            )
            selected_index = source_labels.index(selected_source_label)
            selected_source = source_options[selected_index]
        else:
            st.caption("No source selected.")
    with import_cols[3]:
        max_batch_chars = st.number_input(
            "Max batch chars",
            min_value=500,
            max_value=20000,
            value=DEFAULT_UI_MAX_BATCH_CHARS,
            step=100,
            key="kf_max_batch_chars",
        )
    process_all = st.checkbox(
        "Process all batches",
        value=False,
        key="kf_process_all",
        help="When checked, ignores the max-batches limit and processes every usable batch.",
    )
    max_batches_option = st.selectbox(
        "Max batches to process",
        options=tuple(MAX_BATCHES_UI_OPTIONS.keys()),
        index=tuple(MAX_BATCHES_UI_OPTIONS.keys()).index(DEFAULT_MAX_BATCHES_UI_OPTION),
        key="kf_max_batches_option",
        disabled=process_all,
    )
    force_recompile = st.checkbox(
        "Force recompile",
        value=False,
        key="kf_force_recompile",
    )
    review_mode_option = st.selectbox(
        "Review Mode",
        options=tuple(REVIEW_MODE_UI_OPTIONS.keys()),
        index=tuple(REVIEW_MODE_UI_OPTIONS.keys()).index(DEFAULT_REVIEW_MODE_UI_OPTION),
        key="kf_review_mode_option",
        help="Conservative: known ACT mechanisms only. Normal: known + strong novel. Aggressive: broader exploration.",
    )
    auto_approve = st.checkbox(
        "Auto approve consolidated candidates",
        value=False,
        key="kf_auto_approve",
        help="Only psychotherapy_tle text candidates meeting safety gates are auto-approved.",
    )
    force_single_auto = st.checkbox(
        "Allow single-evidence auto approve (testing)",
        value=False,
        key="kf_force_single_auto_approve",
        disabled=not auto_approve,
    )
    compile_scope = st.radio(
        "Compile scope",
        options=("Document", "Family", "Domain", "Entire Library"),
        horizontal=True,
        key="kf_compile_scope",
    )

    if selected_source is not None:
        supported_text_domain = selected_source.domain in {
            "psychotherapy",
            "psychedelic_research",
            "vocal_icaro",
        }
        supported_compile_source = (
            selected_source.source_type == "text" and supported_text_domain
        ) or (
            selected_source.source_type == "audio_extract"
            and selected_source.domain == "vocal_icaro"
        )
        st.write(
            {
                "source_id": selected_source.source_id,
                "title": selected_source.title,
                "domain": selected_source.domain,
                "family": selected_source.family,
                "source_type": selected_source.source_type,
                "compile_status": selected_source.compile_status,
                "relative_path": selected_source.relative_path,
                "checksum": selected_source.checksum,
                "file_size": selected_source.file_size,
            }
        )
        if not supported_compile_source:
            st.warning(
                f"Unsupported compile route `{selected_source.domain}/{selected_source.source_type}`. "
                "Browsing is enabled, but compilation is disabled until this route is mapped."
            )
    else:
        supported_compile_source = False

    action_cols = st.columns(3)
    if action_cols[0].button(
        "Import / Preview",
        use_container_width=True,
        key="kf_import_segments",
    ):
        if selected_source is None:
            st.session_state.kf_message = "Select a Knowledge Library source first."
        elif selected_source.source_type != "text":
            st.session_state.kf_message = (
                "Audio extract import/preview is not implemented yet. "
                "Use Compile to create an audio-vocal review proposal."
            )
        else:
            try:
                import_result = import_knowledge_source_for_ui(
                    selected_source.source_id,
                    workspace_root,
                    max_batch_chars=int(max_batch_chars),
                )
                st.session_state.kf_last_import = import_result
                st.session_state.kf_message = (
                    f"Imported {import_result.source_id}: "
                    f"{import_result.usable_segments} usable segments, "
                    f"{len(import_result.batch_groups)} batches."
                )
                st.rerun()
            except (FileNotFoundError, ValueError) as exc:
                st.session_state.kf_message = str(exc)

    if action_cols[1].button(
        "Compile",
        type="primary",
        use_container_width=True,
        key="kf_run_extraction",
    ):
        if compile_scope == "Document" and selected_source is None:
            st.session_state.kf_message = "Select a Knowledge Library source first."
        elif compile_scope in {"Family", "Domain"} and not selected_domain:
            st.session_state.kf_message = "Select a Knowledge Library domain first."
        elif compile_scope == "Family" and not selected_family:
            st.session_state.kf_message = "Select a Knowledge Library family first."
        elif compile_scope == "Document" and not supported_compile_source:
            st.session_state.kf_message = (
                f"Unsupported compile route: "
                f"{selected_source.domain}/{selected_source.source_type}"
            )
        elif compile_scope in {"Family", "Domain"} and selected_domain not in {
            "psychotherapy",
            "psychedelic_research",
            "vocal_icaro",
        }:
            st.session_state.kf_message = f"Unsupported knowledge domain: {selected_domain}"
        else:
            try:
                compiler = KnowledgeCompiler(workspace_root=workspace_root)
                max_batches = None if process_all else parse_max_batches_option(max_batches_option)
                progress_started_at = perf_counter()
                progress_events: list[CompileProgressEvent] = []
                progress_bar = st.progress(0.0, text="Starting Knowledge Compiler...")
                status_text = st.empty()
                metric_cols = st.columns(5)
                total_metric = metric_cols[0].empty()
                processed_metric = metric_cols[1].empty()
                reviews_metric = metric_cols[2].empty()
                failed_metric = metric_cols[3].empty()
                elapsed_metric = metric_cols[4].empty()
                event_log_panel = st.empty()

                def _render_progress(event: CompileProgressEvent) -> None:
                    progress_events.append(event)
                    if event.batch_total > 0 and event.batch_index > 0:
                        pct = min(event.batch_index / event.batch_total, 1.0)
                    elif event.event in {PROGRESS_COMPLETED, PROGRESS_FAILED}:
                        pct = 1.0
                    else:
                        pct = 0.0
                    status_label = event.message or event.event.replace("_", " ")
                    progress_bar.progress(
                        pct,
                        text=f"Batch {event.batch_index} / {event.batch_total} — {status_label}"
                        if event.batch_total
                        else status_label,
                    )
                    status_text.markdown(f"**{status_label}**")
                    total_metric.metric("Total batches", event.batch_total or "—")
                    processed_metric.metric(
                        "Processed",
                        event.reviews_created_so_far
                        + event.failed_batches_so_far
                        + event.skipped_reviews_so_far,
                    )
                    reviews_metric.metric("Reviews created", event.reviews_created_so_far)
                    failed_metric.metric("Failed", event.failed_batches_so_far)
                    elapsed_metric.metric(
                        "Elapsed (s)",
                        round(perf_counter() - progress_started_at, 1),
                    )
                    event_lines = [
                        f"{item.timestamp} · {item.event} · {item.message}"
                        for item in progress_events
                    ]
                    event_log_panel.code("\n".join(event_lines[-25:]), language="text")

                compile_kwargs = {
                    "force": force_recompile,
                    "max_batch_chars": int(max_batch_chars),
                    "process_all_batches": process_all,
                    "max_batches": max_batches,
                    "progress_callback": _render_progress,
                    "review_mode": parse_review_mode_option(review_mode_option),
                    "auto_approve": auto_approve,
                    "force_allow_single_evidence_auto_approve": force_single_auto,
                }
                if compile_scope == "Document":
                    summary = compiler.compile_document(
                        selected_source.source_id,
                        **compile_kwargs,
                    )
                elif compile_scope == "Family":
                    summary = compiler.compile_family(
                        selected_domain,
                        selected_family,
                        **compile_kwargs,
                    )
                elif compile_scope == "Domain":
                    summary = compiler.compile_domain(
                        selected_domain,
                        **compile_kwargs,
                    )
                else:
                    summary = compiler.compile_library(**compile_kwargs)

                st.session_state.kf_compile_summary = summary
                if summary.document_results:
                    ui_summary = compile_progress_ui_summary(summary.document_results[0])
                    st.session_state.kf_compile_ui_summary = ui_summary
                st.session_state.kf_compile_funnel = compile_summary_ui_funnel(summary)
                st.session_state.kf_message = (
                    f"Compile finished: {summary.raw_extractions} raw extractions "
                    f"({summary.filtered_extractions} filtered) → "
                    f"{summary.consolidated_candidates} consolidated candidates → "
                    f"{summary.pending_reviews} pending, {summary.auto_approved} auto-approved."
                )
                st.rerun()
            except (FileNotFoundError, ValueError) as exc:
                st.session_state.kf_message = str(exc)

    if action_cols[2].button(
        "Archive pending reviews",
        use_container_width=True,
        key="kf_archive_pending_reviews",
    ):
        try:
            archive_result = archive_pending_reviews_for_ui(workspace_root)
            st.session_state.kf_archived_reviews = (
                st.session_state.get("kf_archived_reviews", 0) + archive_result.archived_count
            )
            st.session_state.kf_message = (
                f"Archived {archive_result.archived_count} pending review(s) to "
                f"{archive_result.archive_dir or '—'}."
            )
            st.rerun()
        except OSError as exc:
            st.session_state.kf_message = str(exc)

    compile_summary = st.session_state.kf_compile_summary
    compile_ui_summary = st.session_state.kf_compile_ui_summary
    compile_funnel = st.session_state.get("kf_compile_funnel")
    if compile_funnel is not None:
        archived_reviews = st.session_state.get("kf_archived_reviews", 0)
        funnel_cols = st.columns(8)
        funnel_cols[0].metric("Chunks scanned", compile_funnel["chunks_seen"])
        funnel_cols[1].metric("Skipped chunks", compile_funnel["chunks_skipped"])
        funnel_cols[2].metric("Extracted chunks", compile_funnel["chunks_extracted"])
        funnel_cols[3].metric("Raw extractions", compile_funnel["raw_extractions"])
        funnel_cols[4].metric("Filtered", compile_funnel["filtered_extractions"])
        funnel_cols[5].metric("Consolidated", compile_funnel["consolidated_candidates"])
        funnel_cols[6].metric("Pending reviews", compile_funnel["pending_reviews"])
        funnel_cols[7].metric("Auto-approved", compile_funnel["auto_approved"])
        skip_reasons = compile_funnel.get("skipped_by_reason") or ()
        if skip_reasons:
            st.markdown("**Skip reasons**")
            st.dataframe(
                [
                    {"reason": reason, "count": count}
                    for reason, count in skip_reasons
                ],
                use_container_width=True,
                hide_index=True,
            )
        relevance_cols = st.columns(3)
        relevance_cols[0].metric("High relevance", compile_funnel.get("high_relevance_count", 0))
        relevance_cols[1].metric("Medium relevance", compile_funnel.get("medium_relevance_count", 0))
        relevance_cols[2].metric("Low relevance", compile_funnel.get("low_relevance_count", 0))
        if archived_reviews:
            st.caption(f"Archived reviews this session: {archived_reviews}")
    if compile_ui_summary is not None:
        st.success("Compile complete.")
        st.write(
            {
                "source_id": compile_ui_summary.source_id,
                "source_type": compile_ui_summary.source_type,
                "domain": compile_ui_summary.domain,
                "knowledge_domain": compile_ui_summary.knowledge_domain,
                "status": compile_ui_summary.status,
                "raw_corpus_path": compile_ui_summary.raw_corpus_path,
                "log_path": compile_ui_summary.log_path,
                "live_log_path": compile_ui_summary.live_log_path,
                "total_batches": compile_ui_summary.total_batches,
                "processed": compile_ui_summary.processed,
                "reviews_created": compile_ui_summary.reviews_created,
                "raw_extractions": compile_ui_summary.raw_extractions,
                "consolidated_candidates": compile_ui_summary.consolidated_candidates,
                "books_processed": compile_ui_summary.books_processed,
                "failed_batches": compile_ui_summary.failed,
                "skipped_reviews": compile_ui_summary.skipped,
                "chunks_seen": compile_ui_summary.chunks_seen,
                "chunks_skipped": compile_ui_summary.chunks_skipped,
                "chunks_extracted": compile_ui_summary.chunks_extracted,
                "skipped_by_reason": compile_ui_summary.skipped_by_reason,
                "max_batch_chars": compile_ui_summary.max_batch_chars,
                "max_batches": compile_ui_summary.max_batches,
                "openai_model": compile_ui_summary.openai_model,
                "elapsed_seconds": compile_ui_summary.elapsed_seconds,
            }
        )
        st.info("Next step: Go to the Review section below to inspect pending reviews.")
    if compile_summary is not None:
        st.write(
            {
                "scope": compile_summary.scope,
                "documents_processed": compile_summary.documents_processed,
                "chunks_created": compile_summary.chunks_created,
                "chunks_seen": compile_summary.chunks_seen,
                "chunks_skipped": compile_summary.chunks_skipped,
                "chunks_extracted": compile_summary.chunks_extracted,
                "skipped_by_reason": compile_summary.skipped_by_reason,
                "semantic_extractions": compile_summary.semantic_extractions,
                "raw_extractions": compile_summary.raw_extractions,
                "consolidated_candidates": compile_summary.consolidated_candidates,
                "books_processed": compile_summary.books_processed,
                "pending_reviews": compile_summary.pending_reviews,
                "approved_patterns": compile_summary.approved_patterns,
                "ctpc_generated": compile_summary.ctpc_generated,
                "failed_documents": compile_summary.failed_documents,
                "skipped_documents": compile_summary.skipped_documents,
                "processing_time_seconds": compile_summary.processing_time_seconds,
            }
        )
        if compile_summary.document_results:
            st.dataframe(
                [
                    {
                        "source_id": result.source_id,
                        "source_type": result.source_type,
                        "domain": result.domain,
                        "knowledge_domain": result.knowledge_domain,
                        "status": result.status,
                        "raw_corpus_path": result.raw_corpus_path,
                        "segment_count": result.segment_count,
                        "usable_batch_count": result.usable_batch_count,
                        "max_batch_chars": result.max_batch_chars,
                        "process_all_batches": result.process_all_batches,
                        "openai_model": result.openai_model,
                        "extraction_attempted": result.extraction_attempted,
                        "reviews_created": result.reviews_created,
                        "raw_extractions": result.raw_extractions,
                        "consolidated_candidates": result.consolidated_candidates,
                        "books_processed": result.books_processed,
                        "failed_batches": result.failed_batches,
                        "skipped_reviews": result.skipped_reviews,
                        "batches_processed": result.batches_processed,
                        "max_batches": result.max_batches,
                        "log_path": result.log_path,
                        "live_log_path": result.live_log_path,
                    }
                    for result in compile_summary.document_results
                ],
                use_container_width=True,
                hide_index=True,
            )
            for result in compile_summary.document_results:
                if result.failed_batch_errors or result.errors:
                    with st.expander(
                        f"Compile errors for {result.source_id}",
                        expanded=True,
                    ):
                        if result.failed_batch_errors:
                            st.dataframe(
                                [
                                    {
                                        "batch_id": error.batch_id,
                                        "error_type": error.error_type,
                                        "error_message": error.message,
                                    }
                                    for error in result.failed_batch_errors
                                ],
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.write(list(result.errors))

    import_result = st.session_state.kf_last_import
    if import_result is not None:
        with st.expander("Imported segments and batches", expanded=False):
            st.write(
                f"**{import_result.source_id}** — "
                f"{import_result.total_segments} segments, "
                f"{import_result.usable_segments} usable, "
                f"{len(import_result.batch_groups)} batches"
            )
            for batch in import_result.batch_groups:
                st.caption(
                    f"`{batch.batch_segment_id}` · {batch.char_count} chars · "
                    f"{len(batch.included_segment_ids)} segments"
                )

    st.divider()
    st.markdown(f"### {workstation_ui_text('kf_step_extraction', language)}")

    table_items = list_extraction_results_for_ui(workspace_root)
    if not table_items:
        st.caption("No pending reviews. Import a TXT file and run extraction.")
        selected_review_id = None
    else:
        st.dataframe(
            [
                {
                    "mechanism": item.canonical_name or item.mechanism_name or item.function_preview,
                    "ontology_status": item.ontology_status or "—",
                    "source_id": item.source_id,
                    "source_title": item.source_title,
                    "source_family": item.source_family,
                    "segment_id": item.segment_id,
                    "review_type": item.review_type,
                    "mentions": item.mention_count,
                    "books": item.book_count,
                    "families": ", ".join(item.source_families),
                    "knowledge_domain": item.knowledge_domain,
                    "status": item.status,
                    "confidence": round(item.confidence, 2),
                    "suggested_action": item.suggested_action,
                }
                for item in table_items
            ],
            use_container_width=True,
            hide_index=True,
        )
        segment_options = [item.segment_id for item in table_items]
        review_id_by_segment = {item.segment_id: item.review_id for item in table_items}
        default_segment_index = 0
        if st.session_state.kf_selected_review_id is not None:
            for index, item in enumerate(table_items):
                if item.review_id == st.session_state.kf_selected_review_id:
                    default_segment_index = index
                    break
        selected_segment = st.selectbox(
            "Select pattern for review",
            options=segment_options,
            index=default_segment_index,
            key="kf_review_segment_select",
        )
        selected_review_id = review_id_by_segment[selected_segment]
        st.session_state.kf_selected_review_id = selected_review_id

    st.divider()

    if selected_review_id is not None:
        st.markdown(f"### {workstation_ui_text('kf_step_review', language)}")
        detail = load_review_for_ui(selected_review_id, workspace_root)
        review_record = load_review_record(selected_review_id, workspace_root)
        editable = review_is_actionable(detail.status)
        can_approve = review_can_be_approved(review_record)

        header_cols = st.columns([3, 1])
        with header_cols[0]:
            if detail.review_type == "consolidated_candidate":
                st.markdown(
                    f"**Mechanism:** {detail.mechanism_name or detail.canonical_name or detail.therapeutic_function} · "
                    f"**Ontology status:** `{detail.ontology_status or 'unknown'}` · "
                    f"evidence **{detail.mention_count}** · books **{detail.book_count}** · "
                    f"families **{', '.join(detail.source_families) or '—'}** · "
                    f"status `{detail.status}` · domain `{detail.knowledge_domain}`"
                )
            else:
                st.markdown(
                    f"**Mechanism:** {detail.mechanism_name or detail.therapeutic_function} · "
                    f"**Ontology status:** `{detail.ontology_status or 'unknown'}` · "
                    f"confidence **{detail.confidence:.2f}** · "
                    f"status `{detail.status}` · domain `{detail.knowledge_domain}` · "
                    f"action hint `{next((item.suggested_action for item in table_items if item.review_id == selected_review_id), '—')}`"
                )
        with header_cols[1]:
            st.caption(f"source: `{detail.source_id}`")

        evidence_col, fields_col = st.columns([1.1, 1])
        with evidence_col:
            if detail.mechanism_name or detail.mechanism_description:
                st.markdown("**Mechanism knowledge**")
                if detail.mechanism_name:
                    st.markdown(f"**Name:** {detail.mechanism_name}")
                if detail.mechanism_description:
                    st.caption(detail.mechanism_description)
                if detail.ontology_mechanism_id:
                    st.caption(f"Ontology ID: `{detail.ontology_mechanism_id}`")
            if detail.why_this_is_a_mechanism or detail.causal_process:
                st.markdown("**Reason for extraction**")
                if detail.why_this_is_a_mechanism:
                    st.info(detail.why_this_is_a_mechanism)
                if detail.causal_process:
                    st.markdown("**Causal explanation**")
                    st.write(detail.causal_process)
            if detail.why_extracted:
                st.markdown("**Gate reasoning**")
                st.info(detail.why_extracted)
                if detail.knowledge_kind or detail.relevance_score:
                    st.caption(
                        f"Relevance: {detail.relevance_score:.2f} · "
                        f"kind `{detail.knowledge_kind or 'unknown'}`"
                    )
                if detail.evidence_span:
                    st.caption(f"Gate evidence: {detail.evidence_span}")
            if detail.evidence_fragments:
                st.markdown("**Evidence fragments**")
                with st.expander(
                    f"Found {detail.mention_count} time(s) across {detail.book_count} book(s)",
                    expanded=True,
                ):
                    st.code("\n\n".join(detail.evidence_fragments), language="text")
            st.markdown("**Evidence summary**")
            st.text_area(
                "evidence_text",
                value=detail.evidence_text,
                height=280,
                disabled=True,
                label_visibility="collapsed",
                key=f"kf_evidence_{detail.review_id}",
            )
            reviewer_notes = st.text_input(
                "Reviewer notes",
                value=detail.reviewer_notes,
                disabled=not editable,
                key=f"kf_notes_{detail.review_id}",
            )
            if editable and not is_compilable_knowledge_domain(review_record.knowledge_domain):
                st.warning(
                    "This review has unknown knowledge domain. Assign a domain before approval."
                )
                assign_labels = [label for _, label in _KF_DOMAIN_OPTIONS]
                assign_by_label = {label: value for value, label in _KF_DOMAIN_OPTIONS}
                assign_label = st.selectbox(
                    "Assign knowledge domain",
                    options=assign_labels,
                    key=f"kf_assign_domain_{detail.review_id}",
                )
                if st.button(
                    "Save domain",
                    key=f"kf_save_domain_{detail.review_id}",
                ):
                    try:
                        assign_review_domain_for_ui(
                            selected_review_id,
                            assign_by_label[assign_label],
                            workspace_root,
                        )
                        st.session_state.kf_message = (
                            f"Assigned domain `{assign_by_label[assign_label]}` "
                            f"to `{detail.segment_id}`."
                        )
                        st.rerun()
                    except HumanReviewError as exc:
                        st.session_state.kf_message = str(exc)
            elif editable and not can_approve:
                st.warning("This review cannot be approved until domain is assigned.")
            action_cols = st.columns(3)
            approve_clicked = (
                editable
                and can_approve
                and action_cols[0].button(
                    workstation_ui_text("kf_approve_compile", language),
                    type="primary",
                    use_container_width=True,
                    key=f"kf_approve_{detail.review_id}",
                )
            )
            reject_clicked = editable and action_cols[1].button(
                workstation_ui_text("kf_reject", language),
                use_container_width=True,
                key=f"kf_reject_{detail.review_id}",
            )
            changes_clicked = (
                detail.status == "pending"
                and action_cols[2].button(
                    workstation_ui_text("kf_request_changes", language),
                    use_container_width=True,
                    key=f"kf_changes_{detail.review_id}",
                )
            )

        with fields_col:
            therapeutic_function = st.text_area(
                "therapeutic_function",
                value=detail.therapeutic_function,
                height=72,
                disabled=not editable,
                key=f"kf_tf_{detail.review_id}",
            )
            psychological_function = st.text_area(
                "psychological_function",
                value=detail.psychological_function,
                height=72,
                disabled=not editable,
                key=f"kf_pf_{detail.review_id}",
            )
            rule_cols = st.columns(2)
            with rule_cols[0]:
                generation_rules = st.text_area(
                    "generation_rules",
                    value=format_multiline_field(detail.generation_rules),
                    height=88,
                    disabled=not editable,
                    key=f"kf_gr_{detail.review_id}",
                )
                voice_rules = st.text_area(
                    "voice_rules",
                    value=format_multiline_field(detail.voice_rules),
                    height=72,
                    disabled=not editable,
                    key=f"kf_vr_{detail.review_id}",
                )
                pause_rules = st.text_area(
                    "pause_rules",
                    value=format_multiline_field(detail.pause_rules),
                    height=72,
                    disabled=not editable,
                    key=f"kf_pr_{detail.review_id}",
                )
            with rule_cols[1]:
                repetition_rules = st.text_area(
                    "repetition_rules",
                    value=format_multiline_field(detail.repetition_rules),
                    height=88,
                    disabled=not editable,
                    key=f"kf_rr_{detail.review_id}",
                )
                symbolic_elements = st.text_area(
                    "symbolic_elements",
                    value=format_multiline_field(detail.symbolic_elements),
                    height=72,
                    disabled=not editable,
                    key=f"kf_se_{detail.review_id}",
                )
                if detail.candidate_targets:
                    st.markdown("**candidate_targets**")
                    for target in detail.candidate_targets:
                        st.caption(f"· {target}")
                else:
                    st.caption("candidate_targets: —")

        with st.expander("Review metadata", expanded=False):
            st.write(f"review_id: `{detail.review_id}`")
            st.write(f"extraction_id: `{detail.extraction_id}`")
            st.write(f"file: `{detail.filename}`")

        if approve_clicked:
            try:
                record = load_review_record(selected_review_id, workspace_root)
                base = base_extraction_for_review(record)
                edited = build_edited_extraction(
                    base,
                    therapeutic_function=therapeutic_function,
                    psychological_function=psychological_function,
                    generation_rules=parse_multiline_field(generation_rules),
                    voice_rules=parse_multiline_field(voice_rules),
                    pause_rules=parse_multiline_field(pause_rules),
                    repetition_rules=parse_multiline_field(repetition_rules),
                    symbolic_elements=parse_multiline_field(symbolic_elements),
                )
                result = approve_review_for_ui(
                    selected_review_id,
                    workspace_root,
                    reviewer_notes=reviewer_notes.strip(),
                    edited_extraction=edited,
                )
                st.session_state.kf_message = (
                    f"Approved and compiled CTPC: `{result.pattern.pattern_id}`"
                )
                st.session_state.kf_selected_review_id = None
                st.rerun()
            except HumanReviewError as exc:
                st.session_state.kf_message = str(exc)
            except CTPCCompilationValidationError as exc:
                st.session_state.kf_message = str(exc)
            except ValueError as exc:
                st.session_state.kf_message = str(exc)

        if reject_clicked:
            try:
                reject_review_for_ui(
                    selected_review_id,
                    workspace_root,
                    notes=reviewer_notes.strip(),
                )
                st.session_state.kf_message = (
                    f"Rejected review for `{detail.segment_id}`."
                )
                st.session_state.kf_selected_review_id = None
                st.rerun()
            except HumanReviewError as exc:
                st.session_state.kf_message = str(exc)

        if changes_clicked:
            try:
                request_changes_for_ui(
                    selected_review_id,
                    workspace_root,
                    notes=reviewer_notes.strip(),
                )
                st.session_state.kf_message = (
                    f"Requested changes on `{detail.segment_id}`."
                )
                st.rerun()
            except HumanReviewError as exc:
                st.session_state.kf_message = str(exc)
    else:
        st.markdown(f"### {workstation_ui_text('kf_step_review', language)}")
        st.caption("Select a batch in step 2 to review evidence and extraction fields.")

    st.divider()
    st.markdown(f"### {workstation_ui_text('kf_step_ctpc', language)}")
    summary = summarize_workspace(workspace_root)
    ctpc_cols = st.columns(4)
    ctpc_cols[0].metric("CTPC patterns", summary.ctpc_pattern_count)
    ctpc_cols[1].metric("Approved reviews", summary.approved_review_count)
    ctpc_cols[2].metric("Pending reviews", summary.pending_review_count)
    ctpc_cols[3].metric("Raw corpus files", summary.raw_corpus_count)

    latest_patterns = list_latest_ctpc_patterns(workspace_root)
    if latest_patterns:
        st.dataframe(
            [
                {
                    "segment_id": item.segment_id,
                    "knowledge_domain": item.knowledge_domain,
                    "therapeutic_function": item.therapeutic_function,
                    "confidence": round(item.confidence, 2),
                    "pattern_id": item.pattern_id,
                }
                for item in latest_patterns
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No compiled CTPC patterns yet.")


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
    (
        workstation_ui_text("knowledge_factory", language),
        WORKSTATION_MODE_KNOWLEDGE_FACTORY,
    ),
]
workstation_value_by_label = {label: value for label, value in workstation_options}
workstation_index_by_mode = {
    WORKSTATION_MODE_GUIDED: 0,
    WORKSTATION_MODE_QUICK_DEMO: 1,
    WORKSTATION_MODE_KNOWLEDGE_FACTORY: 2,
}
default_workstation_index = workstation_index_by_mode.get(
    st.session_state.workstation_mode,
    0,
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

if selected_workstation_mode == WORKSTATION_MODE_KNOWLEDGE_FACTORY:
    _render_knowledge_factory(language)
elif selected_workstation_mode == WORKSTATION_MODE_QUICK_DEMO:
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
