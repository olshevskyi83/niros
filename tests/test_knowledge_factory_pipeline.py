"""Integration tests for Knowledge Factory pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from niros.ctpc_compiler import compile_pattern_from_approved_review
from niros.human_review_workflow import build_review_id
from niros.knowledge_domain import ctpc_pattern_relative_path
from niros.knowledge_factory_pipeline import KnowledgeFactoryPipeline
from niros.raw_source import RawSourceCorpus
from niros.therapeutic_extraction import TherapeuticFunctionExtraction


class FakeChatCompletionClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def complete(self, *, model: str, messages: list[dict[str, str]]) -> str:
        self.calls.append({"model": model, "messages": messages})
        return self.response


def _write_text_pdf(path: Path, page_texts: list[str]) -> None:
    parts: list[bytes] = []

    def add(text: str) -> None:
        parts.append(text.encode("latin-1"))

    add("%PDF-1.4\n")
    offsets: dict[int, int] = {}

    def add_obj(number: int, body: str) -> None:
        offsets[number] = sum(len(part) for part in parts)
        add(f"{number} 0 obj\n{body}\nendobj\n")

    page_count = len(page_texts)
    font_number = 2 + (2 * page_count) + 1
    kids = " ".join(f"{3 + (2 * index)} 0 R" for index in range(page_count))

    add_obj(1, "<< /Type /Catalog /Pages 2 0 R >>")
    add_obj(2, f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>")

    for index, text in enumerate(page_texts):
        page_number = 3 + (2 * index)
        content_number = page_number + 1
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 {720 - (index * 24)} Td ({escaped}) Tj ET"
        add_obj(
            page_number,
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_number} 0 R >> >> "
                f"/Contents {content_number} 0 R >>"
            ),
        )
        add_obj(
            content_number,
            f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        )

    add_obj(font_number, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    xref_offset = sum(len(part) for part in parts)
    add("xref\n")
    add(f"0 {font_number + 1}\n")
    add("0000000000 65535 f \n")
    for number in range(1, font_number + 1):
        add(f"{offsets[number]:010d} 00000 n \n")
    add(f"trailer\n<< /Size {font_number + 1} /Root 1 0 R >>\n")
    add("startxref\n")
    add(f"{xref_offset}\n")
    add("%%EOF\n")
    path.write_bytes(b"".join(parts))


def _valid_llm_json() -> str:
    payload = {
        "therapeutic_function": "self_compassion",
        "psychological_function": "reduce self-criticism",
        "symbolic_elements": ["heart", "water"],
        "candidate_targets": ["shame"],
        "generation_rules": ["Use gentle second-person phrasing."],
        "voice_rules": ["Keep tempo slow and supportive."],
        "repetition_rules": ["Repeat key phrase."],
        "pause_rules": ["Pause after invocation."],
        "contraindications": ["acute crisis"],
        "confidence": 0.85,
    }
    return json.dumps(payload)


def test_knowledge_factory_pipeline_end_to_end_offline(tmp_path: Path) -> None:
    root = tmp_path / "knowledge_factory"
    pdf_path = tmp_path / "sample.pdf"
    page_text = "May the heart be softened and fear released."
    _write_text_pdf(pdf_path, [page_text])

    fake_client = FakeChatCompletionClient(response=_valid_llm_json())
    pipeline = KnowledgeFactoryPipeline.from_workspace_root(
        str(root),
        extraction_client=fake_client,
        timestamp_fn=lambda: "2026-07-06T12:00:00+00:00",
    )

    first = pipeline.run_from_pdf(
        pdf_path,
        source_id="source_001",
        source_title="Sample PDF",
        source_family="research",
        reviewer_id="reviewer_001",
        reviewer_notes="Approved in integration test.",
    )
    second = pipeline.run_from_pdf(
        pdf_path,
        source_id="source_001",
        source_title="Sample PDF",
        source_family="research",
        reviewer_id="reviewer_001",
        reviewer_notes="Approved in integration test.",
    )

    assert isinstance(first.raw_source_corpus, RawSourceCorpus)
    assert len(first.raw_source_corpus.segments) == 1
    assert first.raw_source_corpus.segments[0].raw_text == page_text

    assert isinstance(first.therapeutic_function_extraction, TherapeuticFunctionExtraction)
    assert first.therapeutic_function_extraction.therapeutic_function == "self_compassion"
    assert first.therapeutic_function_extraction.segment_id == "source_001_page_001"
    assert first.therapeutic_function_extraction.evidence_text == page_text

    review_id = build_review_id(first.therapeutic_function_extraction.extraction_id)
    review_path = Path(pipeline.review_workflow.paths.review_dir) / f"{review_id}.json"
    assert review_path.exists()

    pattern_id = first.canonical_therapeutic_pattern.pattern_id
    relative = ctpc_pattern_relative_path(
        first.canonical_therapeutic_pattern.knowledge_domain,
        pattern_id,
    )
    ctpc_path = Path(pipeline.ctpc_compiler.paths.ctpc_dir) / relative
    assert ctpc_path.exists()

    expected_pattern = compile_pattern_from_approved_review(first.human_review_record)
    assert first.canonical_therapeutic_pattern == expected_pattern
    assert pipeline.ctpc_compiler.load_pattern(pattern_id) == expected_pattern

    assert len(fake_client.calls) == 2
    assert first == second
