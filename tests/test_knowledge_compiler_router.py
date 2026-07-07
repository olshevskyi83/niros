"""Tests for typed Knowledge Compiler routing."""

from __future__ import annotations

from niros.knowledge_compiler_router import (
    AudioExtractCompiler,
    TextSemanticCompiler,
    route_knowledge_source,
)
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    KNOWLEDGE_DOMAIN_VOCAL_ICARO,
)
from niros.knowledge_library import KnowledgeLibrarySourceRecord


def _source(domain: str, source_type: str) -> KnowledgeLibrarySourceRecord:
    extension = ".audio_extract.json" if source_type == "audio_extract" else ".txt"
    filename = f"source{extension}"
    return KnowledgeLibrarySourceRecord(
        source_id=f"source_{domain}_{source_type}",
        title="source",
        domain=domain,
        family="general",
        source_type=source_type,
        relative_path=f"{domain}/{filename}",
        filename=filename,
        checksum="checksum",
        extension=extension,
    )


def test_psychotherapy_text_routes_to_psychotherapy_tle_text_compiler() -> None:
    route = route_knowledge_source(_source("psychotherapy", "text"))

    assert route.supported
    assert isinstance(route.compiler, TextSemanticCompiler)
    assert route.knowledge_domain == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE


def test_psychedelic_research_text_routes_to_psychotherapy_tle_text_compiler() -> None:
    route = route_knowledge_source(_source("psychedelic_research", "text"))

    assert route.supported
    assert isinstance(route.compiler, TextSemanticCompiler)
    assert route.knowledge_domain == KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE


def test_vocal_icaro_text_routes_to_vocal_icaro_text_compiler() -> None:
    route = route_knowledge_source(_source("vocal_icaro", "text"))

    assert route.supported
    assert isinstance(route.compiler, TextSemanticCompiler)
    assert route.knowledge_domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO


def test_vocal_icaro_audio_extract_routes_to_audio_extract_compiler() -> None:
    route = route_knowledge_source(_source("vocal_icaro", "audio_extract"))

    assert route.supported
    assert isinstance(route.compiler, AudioExtractCompiler)
    assert route.knowledge_domain == KNOWLEDGE_DOMAIN_VOCAL_ICARO


def test_music_session_text_is_compile_unsupported() -> None:
    route = route_knowledge_source(_source("music_session", "text"))

    assert not route.supported
    assert "music_session/text" in route.unsupported_reason


def test_physiology_text_is_compile_unsupported() -> None:
    route = route_knowledge_source(_source("physiology", "text"))

    assert not route.supported
    assert "physiology/text" in route.unsupported_reason


def test_unknown_domain_is_compile_unsupported() -> None:
    route = route_knowledge_source(_source("unknown_domain", "text"))

    assert not route.supported
    assert "unknown_domain/text" in route.unsupported_reason
