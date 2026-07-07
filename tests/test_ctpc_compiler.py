"""Tests for CTPC compiler."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from niros.ctpc import CanonicalTherapeuticPattern
from niros.ctpc_compiler import (
    COMPILED_CTPC_REVIEW_STATUS,
    CTPCCompilationStateError,
    CTPCCompiler,
    compile_pattern_from_approved_review,
)
from niros.human_review_workflow import (
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_CHANGES_REQUESTED,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_REJECTED,
    HumanReviewRecord,
    build_review_id,
)
from niros.knowledge_workspace import ensure_knowledge_workspace
from niros.therapeutic_extraction import TherapeuticFunctionExtraction, build_extraction_id


def _extraction(**overrides) -> TherapeuticFunctionExtraction:
    source_id = overrides.get("source_id", "source_001")
    segment_id = overrides.get("segment_id", "source_001_segment_001")
    therapeutic_function = overrides.get("therapeutic_function", "self_compassion")
    psychological_function = overrides.get("psychological_function", "reduce self-criticism")
    base = {
        "extraction_id": build_extraction_id(
            source_id,
            segment_id,
            therapeutic_function,
            psychological_function,
        ),
        "source_id": source_id,
        "segment_id": segment_id,
        "therapeutic_function": therapeutic_function,
        "evidence_text": "May the heart be softened and fear released.",
        "psychological_function": psychological_function,
        "generation_rules": ("Use gentle second-person phrasing.",),
        "voice_rules": ("Keep tempo slow and supportive.",),
        "symbolic_elements": ("heart", "water"),
        "confidence": 0.85,
        "extractor": "openai",
    }
    base.update(overrides)
    return TherapeuticFunctionExtraction(**base)


def _approved_review(
    *,
    edited_extraction: TherapeuticFunctionExtraction | None = None,
) -> HumanReviewRecord:
    return HumanReviewRecord(
        review_id=build_review_id(_extraction().extraction_id),
        extraction_id=_extraction().extraction_id,
        source_id="source_001",
        segment_id="source_001_segment_001",
        status=REVIEW_STATUS_APPROVED,
        original_extraction=_extraction(),
        edited_extraction=edited_extraction,
        reviewer_id="reviewer_001",
    )


def _review_with_status(status: str) -> HumanReviewRecord:
    return HumanReviewRecord(
        review_id=build_review_id(_extraction().extraction_id),
        extraction_id=_extraction().extraction_id,
        source_id="source_001",
        segment_id="source_001_segment_001",
        status=status,
        original_extraction=_extraction(),
    )


def _compiler(tmp_path: Path) -> CTPCCompiler:
    root = tmp_path / "knowledge_factory"
    paths = ensure_knowledge_workspace(str(root))
    return CTPCCompiler(paths=paths)


def test_approved_review_compiles_successfully(tmp_path: Path) -> None:
    compiler = _compiler(tmp_path)
    pattern = compiler.compile_review(_approved_review())

    assert isinstance(pattern, CanonicalTherapeuticPattern)
    assert pattern.pattern_id == f"ctp_from_{_extraction().extraction_id}"
    assert pattern.therapeutic_function == "self_compassion"
    assert pattern.review_status == COMPILED_CTPC_REVIEW_STATUS
    assert compiler._pattern_path(pattern.pattern_id).exists()


@pytest.mark.parametrize(
    "status",
    [REVIEW_STATUS_PENDING, REVIEW_STATUS_REJECTED, REVIEW_STATUS_CHANGES_REQUESTED],
)
def test_non_approved_review_rejected(tmp_path: Path, status: str) -> None:
    compiler = _compiler(tmp_path)

    with pytest.raises(CTPCCompilationStateError):
        compiler.compile_review(_review_with_status(status))


def test_edited_extraction_is_compiled_instead_of_original(tmp_path: Path) -> None:
    compiler = _compiler(tmp_path)
    edited = _extraction(
        psychological_function="increase emotional safety",
        symbolic_elements=("heart", "light"),
    )
    pattern = compiler.compile_review(_approved_review(edited_extraction=edited))

    assert pattern.psychological_function == "increase emotional safety"
    assert pattern.symbolic_elements == ("heart", "light")


def test_saved_ctpc_json_reloads_correctly(tmp_path: Path) -> None:
    compiler = _compiler(tmp_path)
    compiled = compiler.compile_review(_approved_review())

    loaded = compiler.load_pattern(compiled.pattern_id)
    assert loaded == compiled


def test_compiler_does_not_touch_review_folder(tmp_path: Path) -> None:
    compiler = _compiler(tmp_path)
    review_dir = Path(compiler.paths.review_dir)
    review_dir.mkdir(parents=True, exist_ok=True)
    marker = review_dir / "existing_review.json"
    marker.write_text("{}", encoding="utf-8")

    compiler.compile_review(_approved_review())

    assert list(review_dir.iterdir()) == [marker]


def test_compiler_never_calls_openai() -> None:
    import niros.ctpc_compiler as ctpc_compiler_module

    source = inspect.getsource(ctpc_compiler_module)
    assert "openai" not in source.lower()
    assert "OpenAI" not in source


def test_compile_pattern_from_approved_review_is_deterministic() -> None:
    record = _approved_review()
    first = compile_pattern_from_approved_review(record)
    second = compile_pattern_from_approved_review(record)
    assert first == second
