"""CTPC → UniversalPattern adapter for psychotherapy_tle runtime loading."""

from __future__ import annotations

import json
from pathlib import Path

from niros.ctpc import CanonicalTherapeuticPattern
from niros.ctpc_compiler import deserialize_ctpc_pattern
from niros.knowledge_domain import (
    KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    normalize_review_knowledge_domain,
)
from niros.knowledge_workspace import (
    DEFAULT_KNOWLEDGE_ROOT,
    build_knowledge_workspace_paths,
)
from niros_tle.universal_pattern import (
    ACTIVE_LIBRARY_STATUS,
    SOURCE_TYPE_CTPC,
    UNSPECIFIED_VALUE,
    UniversalPattern,
)


def psychotherapy_tle_ctpc_directory(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> Path:
    """Return the psychotherapy_tle CTPC subdirectory path."""
    paths = build_knowledge_workspace_paths(workspace_root)
    return Path(paths.ctpc_dir) / KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE


def load_psychotherapy_tle_ctpc_patterns(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> tuple[CanonicalTherapeuticPattern, ...]:
    """Load compiled psychotherapy_tle CTPC patterns from the Knowledge Factory workspace."""
    directory = psychotherapy_tle_ctpc_directory(workspace_root)
    if not directory.is_dir():
        return ()

    patterns: list[CanonicalTherapeuticPattern] = []
    for path in sorted(directory.glob("*.json")):
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        pattern = deserialize_ctpc_pattern(data)
        domain = normalize_review_knowledge_domain(pattern.knowledge_domain)
        if domain != KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE:
            continue
        patterns.append(pattern)
    return tuple(patterns)


def ctpc_pattern_to_universal_pattern(
    pattern: CanonicalTherapeuticPattern,
) -> UniversalPattern:
    """Convert one psychotherapy_tle CTPC pattern into a runtime UniversalPattern."""
    source_family = pattern.source_family.strip()
    canonical_name = pattern.name.strip() or pattern.therapeutic_function.replace("_", " ")
    return UniversalPattern(
        pattern_id=pattern.pattern_id,
        canonical_name=canonical_name,
        source_families=(source_family,) if source_family else (),
        member_pattern_ids=(pattern.pattern_id,),
        confidence=pattern.confidence,
        target_signals=(),
        contraindication_signals=tuple(pattern.contraindications),
        fit_domains=(),
        expected_effects=(),
        intervention_style=UNSPECIFIED_VALUE,
        session_phase=UNSPECIFIED_VALUE,
        library_status=ACTIVE_LIBRARY_STATUS,
        source_type=SOURCE_TYPE_CTPC,
        source_reference=pattern.source_reference,
    )


def load_psychotherapy_tle_universal_patterns(
    workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
) -> tuple[UniversalPattern, ...]:
    """Load psychotherapy_tle CTPC patterns as UniversalPattern runtime objects."""
    return tuple(
        ctpc_pattern_to_universal_pattern(pattern)
        for pattern in load_psychotherapy_tle_ctpc_patterns(workspace_root)
    )
