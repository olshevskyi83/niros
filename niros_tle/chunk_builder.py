"""Deterministic Knowledge Chunk Builder — meaningful units, not fixed-size splits."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from niros_tle.corpus_ingestion import SourceDocument

TLE_ROOT = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = TLE_ROOT.parent

CHUNK_TYPES: tuple[str, ...] = (
    "paragraph",
    "exercise",
    "story",
    "dialogue",
    "chant",
    "case",
    "chapter_intro",
    "unknown",
)

MIN_CHUNK_CHARS = 120
MAX_MERGED_CHARS = 900
SENTENCE_END = re.compile(r"[.!?…\"']\s*$")

SECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^chapter\s+[0-9ivxlcdm]+(?:[:\.\-\s]|$)", re.IGNORECASE),
    re.compile(r"^part\s+[0-9ivxlcdm]+(?:[:\.\-\s]|$)", re.IGNORECASE),
    re.compile(r"^#{1,6}\s+.+"),
    re.compile(r"^[A-Z][A-Z0-9\s\-:]{3,60}$"),
)

PAGE_MARKER = re.compile(r"^\[page\s+(\d+)\]\s*$", re.IGNORECASE)
CHANT_BOUNDARY = re.compile(r"^(?:\[icaro\]|icaro:|chant:|---+\s*$|\*{3}\s*$)", re.IGNORECASE)
EXERCISE_START = re.compile(
    r"^(?:exercise|practice|homework|try this|worksheet)\s*[:\.]",
    re.IGNORECASE,
)
STORY_START = re.compile(
    r"^(?:once upon a time|there was|a patient|one day|he told me|she told me)\b",
    re.IGNORECASE,
)
DIALOGUE_LINE = re.compile(r'^(?:[A-Z][a-z]+|Q|A|Client|Therapist)\s*[:\-—]\s*.+')
CASE_START = re.compile(r"^(?:case study|clinical example|client profile)\s*[:\.]?", re.IGNORECASE)


class ChunkBuilderError(ValueError):
    """Raised when chunk building cannot proceed safely."""


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    source_family: str
    language: str
    chunk_type: str
    title: str
    text: str
    page_start: int | None
    page_end: int | None
    section_path: tuple[str, ...]
    sequence_number: int
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "source_family": self.source_family,
            "language": self.language,
            "chunk_type": self.chunk_type,
            "title": self.title,
            "text": self.text,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "section_path": list(self.section_path),
            "sequence_number": self.sequence_number,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class _DraftBlock:
    text: str
    section_path: tuple[str, ...]
    page_start: int | None
    page_end: int | None
    chunk_type: str
    title: str


class ChunkBuilder:
    """Build meaningful knowledge chunks from registered source documents."""

    def __init__(
        self,
        *,
        repo_root: Path | str | None = None,
        min_chunk_chars: int = MIN_CHUNK_CHARS,
    ) -> None:
        self._repo_root = Path(repo_root or DEFAULT_REPO_ROOT)
        self._min_chunk_chars = min_chunk_chars

    def build_chunks(self, document: SourceDocument) -> tuple[KnowledgeChunk, ...]:
        text = load_document_text(document, repo_root=self._repo_root)
        if not text.strip():
            return ()

        blocks = self._parse_blocks(text, document.source_family)
        merged = self._merge_blocks(blocks, document.source_family)
        return self._finalize_chunks(document, merged)

    def save_chunks(
        self,
        document: SourceDocument,
        chunks: tuple[KnowledgeChunk, ...],
    ) -> Path:
        output_path = processed_output_path(document, repo_root=self._repo_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "document_id": document.document_id,
            "source_family": document.source_family,
            "language": document.language,
            "chunk_count": len(chunks),
            "chunks": [chunk.to_dict() for chunk in chunks],
        }
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return output_path

    def build_and_save(self, document: SourceDocument) -> tuple[KnowledgeChunk, ...]:
        chunks = self.build_chunks(document)
        self.save_chunks(document, chunks)
        return chunks

    def _parse_blocks(self, text: str, source_family: str) -> list[_DraftBlock]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if source_family == "maria_sabina":
            return self._parse_maria_sabina_blocks(normalized)
        return self._parse_generic_blocks(normalized, source_family)

    def _parse_generic_blocks(self, text: str, source_family: str) -> list[_DraftBlock]:
        blocks: list[_DraftBlock] = []
        section_path: list[str] = []
        current_page: int | None = None
        paragraph_lines: list[str] = []
        pending_title = ""

        def flush_paragraph() -> None:
            nonlocal paragraph_lines, pending_title
            if not paragraph_lines:
                pending_title = ""
                return
            paragraph_text = "\n".join(paragraph_lines).strip()
            paragraph_lines = []
            if not paragraph_text:
                pending_title = ""
                return

            chunk_type = classify_chunk_type(
                paragraph_text,
                source_family=source_family,
                section_path=tuple(section_path),
                is_first_after_section=bool(pending_title),
            )
            title = pending_title or derive_chunk_title(paragraph_text, chunk_type)
            pending_title = ""
            blocks.append(
                _DraftBlock(
                    text=paragraph_text,
                    section_path=tuple(section_path),
                    page_start=current_page,
                    page_end=current_page,
                    chunk_type=chunk_type,
                    title=title,
                )
            )

        lines = text.split("\n")
        index = 0
        while index < len(lines):
            raw_line = lines[index]
            line = raw_line.strip()

            if not line:
                flush_paragraph()
                index += 1
                continue

            page_match = PAGE_MARKER.match(line)
            if page_match:
                flush_paragraph()
                current_page = int(page_match.group(1))
                index += 1
                continue

            if is_section_heading(line):
                flush_paragraph()
                section_path = [line.rstrip(":").strip()]
                pending_title = line.rstrip(":").strip()
                index += 1
                continue

            if source_family == "act" and EXERCISE_START.match(line):
                flush_paragraph()
                exercise_lines = [raw_line.rstrip()]
                index += 1
                while index < len(lines):
                    next_line = lines[index]
                    if not next_line.strip():
                        if index + 1 < len(lines) and lines[index + 1].strip():
                            peek = lines[index + 1].strip()
                            if is_section_heading(peek) or EXERCISE_START.match(peek):
                                break
                            exercise_lines.append("")
                            index += 1
                            continue
                        break
                    if is_section_heading(next_line.strip()) or EXERCISE_START.match(next_line.strip()):
                        break
                    exercise_lines.append(next_line.rstrip())
                    index += 1
                exercise_text = "\n".join(exercise_lines).strip()
                blocks.append(
                    _DraftBlock(
                        text=exercise_text,
                        section_path=tuple(section_path),
                        page_start=current_page,
                        page_end=current_page,
                        chunk_type="exercise",
                        title=derive_chunk_title(exercise_text, "exercise"),
                    )
                )
                continue

            paragraph_lines.append(raw_line.rstrip())
            index += 1

        flush_paragraph()
        return self._expand_special_blocks(blocks, source_family)

    def _expand_special_blocks(
        self,
        blocks: list[_DraftBlock],
        source_family: str,
    ) -> list[_DraftBlock]:
        expanded: list[_DraftBlock] = []
        index = 0
        while index < len(blocks):
            block = blocks[index]
            if source_family == "act" and block.chunk_type == "exercise":
                merged_lines = [block.text]
                next_index = index + 1
                while next_index < len(blocks):
                    candidate = blocks[next_index]
                    if candidate.chunk_type != "paragraph":
                        break
                    if EXERCISE_START.match(candidate.text.split("\n", 1)[0]):
                        break
                    if len("\n\n".join(merged_lines + [candidate.text])) > MAX_MERGED_CHARS:
                        break
                    merged_lines.append(candidate.text)
                    next_index += 1
                expanded.append(
                    _DraftBlock(
                        text="\n\n".join(merged_lines),
                        section_path=block.section_path,
                        page_start=block.page_start,
                        page_end=blocks[next_index - 1].page_end if next_index > index else block.page_end,
                        chunk_type="exercise",
                        title=block.title or "Exercise",
                    )
                )
                index = next_index
                continue

            if source_family == "erickson" and block.chunk_type in {"story", "paragraph"}:
                if STORY_START.match(block.text) or block.chunk_type == "story":
                    merged_lines = [block.text]
                    next_index = index + 1
                    while next_index < len(blocks):
                        candidate = blocks[next_index]
                        if candidate.chunk_type not in {"story", "paragraph"}:
                            break
                        if is_story_continuation(candidate.text):
                            merged_lines.append(candidate.text)
                            next_index += 1
                            continue
                        break
                    expanded.append(
                        _DraftBlock(
                            text="\n\n".join(merged_lines),
                            section_path=block.section_path,
                            page_start=block.page_start,
                            page_end=blocks[next_index - 1].page_end if next_index > index else block.page_end,
                            chunk_type="story",
                            title=block.title or "Story",
                        )
                    )
                    index = next_index
                    continue

            expanded.append(block)
            index += 1
        return expanded

    def _parse_maria_sabina_blocks(self, text: str) -> list[_DraftBlock]:
        sections = re.split(r"\n\s*\n\s*\n+", text)
        blocks: list[_DraftBlock] = []
        section_path: tuple[str, ...] = ()
        current_page: int | None = None

        for section in sections:
            lines = [line.strip() for line in section.split("\n") if line.strip()]
            if not lines:
                continue

            if len(lines) == 1 and PAGE_MARKER.match(lines[0]):
                current_page = int(PAGE_MARKER.match(lines[0]).group(1))
                continue

            if len(lines) == 1 and is_section_heading(lines[0]):
                section_path = (lines[0].rstrip(":"),)
                continue

            chant_parts: list[list[str]] = [[]]
            for line in lines:
                if CHANT_BOUNDARY.match(line):
                    if chant_parts[-1]:
                        chant_parts.append([])
                    continue
                chant_parts[-1].append(line)

            for part in chant_parts:
                if not part:
                    continue
                chant_text = "\n".join(part).strip()
                if not chant_text:
                    continue
                chunk_type = "chant" if _looks_like_chant(chant_text) else "paragraph"
                blocks.append(
                    _DraftBlock(
                        text=chant_text,
                        section_path=section_path,
                        page_start=current_page,
                        page_end=current_page,
                        chunk_type=chunk_type,
                        title=derive_chunk_title(chant_text, chunk_type),
                    )
                )
        return blocks

    def _merge_blocks(self, blocks: list[_DraftBlock], source_family: str) -> list[_DraftBlock]:
        if source_family == "maria_sabina":
            return blocks

        merged: list[_DraftBlock] = []
        index = 0
        while index < len(blocks):
            current = blocks[index]
            if current.chunk_type in {"exercise", "story", "chant", "case", "chapter_intro"}:
                merged.append(current)
                index += 1
                continue

            combined_text = current.text
            combined_start = current.page_start
            combined_end = current.page_end
            combined_type = current.chunk_type
            combined_title = current.title
            combined_section = current.section_path
            next_index = index + 1

            while (
                next_index < len(blocks)
                and len(combined_text) < self._min_chunk_chars
                and not is_standalone_paragraph(combined_text)
                and blocks[next_index].chunk_type == "paragraph"
                and blocks[next_index].section_path == combined_section
                and not is_standalone_paragraph(blocks[next_index].text)
                and len(combined_text) + len(blocks[next_index].text) + 2 <= MAX_MERGED_CHARS
            ):
                combined_text = f"{combined_text}\n\n{blocks[next_index].text}"
                combined_end = blocks[next_index].page_end or combined_end
                next_index += 1

            merged.append(
                _DraftBlock(
                    text=combined_text,
                    section_path=combined_section,
                    page_start=combined_start,
                    page_end=combined_end,
                    chunk_type=combined_type,
                    title=combined_title,
                )
            )
            index = next_index
        return merged

    def _finalize_chunks(
        self,
        document: SourceDocument,
        blocks: list[_DraftBlock],
    ) -> tuple[KnowledgeChunk, ...]:
        chunks: list[KnowledgeChunk] = []
        for sequence_number, block in enumerate(blocks, start=1):
            chunk_id = f"{document.document_id}_{sequence_number:04d}"
            chunks.append(
                KnowledgeChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    source_family=document.source_family,
                    language=document.language,
                    chunk_type=block.chunk_type,
                    title=block.title,
                    text=block.text,
                    page_start=block.page_start,
                    page_end=block.page_end,
                    section_path=block.section_path,
                    sequence_number=sequence_number,
                    metadata={
                        "source_document": document.document_id,
                        "position": str(sequence_number),
                        "section_hierarchy": " > ".join(block.section_path) if block.section_path else "",
                    },
                )
            )
        return tuple(chunks)


def load_document_text(document: SourceDocument, *, repo_root: Path) -> str:
    """Load plain text for chunking without LLM or embedding steps."""
    raw_path = repo_root / document.file_path
    file_type = document.file_type.lower().lstrip(".")

    if file_type in {"txt", "md"}:
        return raw_path.read_text(encoding="utf-8")

    sidecar = processed_sidecar_text_path(document, repo_root=repo_root)
    if sidecar.exists():
        return sidecar.read_text(encoding="utf-8")

    if file_type in {"pdf", "epub"}:
        return ""
    raise ChunkBuilderError(f"Unsupported file type for chunk building: {file_type}")


def processed_output_path(document: SourceDocument, *, repo_root: Path) -> Path:
    relative = Path(document.file_path)
    source_family = document.source_family
    return repo_root / "niros_tle" / "corpus" / source_family / "processed" / f"{document.document_id}.chunks.json"


def processed_sidecar_text_path(document: SourceDocument, *, repo_root: Path) -> Path:
    return processed_output_path(document, repo_root=repo_root).with_name(
        f"{document.document_id}.source.txt"
    )


def classify_chunk_type(
    text: str,
    *,
    source_family: str,
    section_path: tuple[str, ...],
    is_first_after_section: bool,
) -> str:
    first_line = text.split("\n", 1)[0].strip()
    if source_family == "maria_sabina" and _looks_like_chant(text):
        return "chant"
    if EXERCISE_START.match(first_line) or (source_family == "act" and "worksheet" in first_line.lower()):
        return "exercise"
    if STORY_START.match(first_line) or (source_family == "erickson" and "patient" in first_line.lower()):
        return "story"
    if CASE_START.match(first_line):
        return "case"
    if DIALOGUE_LINE.match(first_line) and "\n" in text:
        return "dialogue"
    if is_first_after_section and len(text) < 400:
        return "chapter_intro"
    return "paragraph"


def derive_chunk_title(text: str, chunk_type: str) -> str:
    first_line = text.split("\n", 1)[0].strip()
    if chunk_type == "chant":
        return first_line[:80] or "Chant"
    if chunk_type == "exercise":
        return first_line[:80] or "Exercise"
    if chunk_type == "story":
        return first_line[:80] or "Story"
    return first_line[:80] or chunk_type.replace("_", " ").title()


def is_standalone_paragraph(text: str, *, min_words: int = 6) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if len(stripped) >= MIN_CHUNK_CHARS:
        return True
    word_count = len(stripped.split())
    return bool(SENTENCE_END.search(stripped)) and word_count >= min_words


def is_section_heading(line: str) -> bool:
    return any(pattern.match(line.strip()) for pattern in SECTION_PATTERNS)


def is_story_continuation(text: str) -> bool:
    first_line = text.split("\n", 1)[0].strip()
    if STORY_START.match(first_line):
        return True
    if first_line.startswith(('"', "'")):
        return True
    if re.match(r"^(?:And then|He|She|They|I)\b", first_line):
        return True
    return not SENTENCE_END.search(first_line)


def _looks_like_chant(text: str) -> bool:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) >= 2 and all(len(line) <= 80 for line in lines):
        short_lines = sum(1 for line in lines if len(line.split()) <= 12)
        return short_lines >= max(2, len(lines) // 2)
    return False
