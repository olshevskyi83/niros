from niros.assessment_domain_map import (
    CORE_PSYCHOLOGICAL_DIMENSIONS,
    CORE_PSYCHOLOGICAL_DOMAIN_IDS,
    FORBIDDEN_DIAGNOSTIC_PHRASES,
    build_assessment_domain_map,
    domain_map_contains_diagnostic_language,
    get_assessment_domain,
)
from niros.knowledge import PatternLoader


def test_all_six_core_psychological_domains_exist():
    domain_map = build_assessment_domain_map()

    for domain_id in CORE_PSYCHOLOGICAL_DOMAIN_IDS:
        assert domain_id in domain_map


def test_all_required_dimensions_exist_per_domain():
    for domain_id, expected_dimensions in CORE_PSYCHOLOGICAL_DIMENSIONS.items():
        domain = get_assessment_domain(domain_id)

        assert domain is not None
        assert domain.fingerprint_dimensions == expected_dimensions


def test_every_core_psychological_domain_maps_to_at_least_one_pattern():
    for domain_id in CORE_PSYCHOLOGICAL_DOMAIN_IDS:
        domain = get_assessment_domain(domain_id)

        assert domain is not None
        assert domain.pattern_ids, f"{domain_id} has no pattern_ids"


def test_every_core_psychological_domain_has_semantic_fact_categories():
    for domain_id in CORE_PSYCHOLOGICAL_DOMAIN_IDS:
        domain = get_assessment_domain(domain_id)

        assert domain is not None
        assert domain.semantic_fact_categories, f"{domain_id} has no semantic_fact_categories"


def test_core_psychological_domains_have_no_diagnostic_wording():
    for domain_id in CORE_PSYCHOLOGICAL_DOMAIN_IDS:
        domain = get_assessment_domain(domain_id)

        assert domain is not None
        combined = f"{domain.title} {domain.purpose}".lower()
        assert not domain_map_contains_diagnostic_language(domain), (
            f"{domain_id} contains forbidden diagnostic language"
        )
        assert not any(phrase in combined for phrase in FORBIDDEN_DIAGNOSTIC_PHRASES)


def test_core_psychological_domain_map_is_deterministic():
    first = {
        domain_id: get_assessment_domain(domain_id)
        for domain_id in CORE_PSYCHOLOGICAL_DOMAIN_IDS
    }
    second = {
        domain_id: build_assessment_domain_map()[domain_id]
        for domain_id in CORE_PSYCHOLOGICAL_DOMAIN_IDS
    }

    assert first == second


def test_core_psychological_domain_pattern_ids_exist_in_knowledge_base():
    known_patterns = frozenset(pattern.canonical_id for pattern in PatternLoader().load_all())

    for domain_id in CORE_PSYCHOLOGICAL_DOMAIN_IDS:
        domain = get_assessment_domain(domain_id)
        assert domain is not None
        missing = [pattern_id for pattern_id in domain.pattern_ids if pattern_id not in known_patterns]
        assert not missing, f"{domain_id} references unknown patterns: {missing}"


def test_self_domain_covers_self_structure_dimensions():
    domain = get_assessment_domain("self_domain")

    assert domain is not None
    assert "self_worth" in domain.fingerprint_dimensions
    assert "shame" in domain.fingerprint_dimensions
    assert "agency" in domain.fingerprint_dimensions
    assert "unworthiness_signal" in domain.pattern_ids
    assert "self" in domain.semantic_fact_categories


def test_emotion_regulation_domain_uses_ders_style_tools():
    domain = get_assessment_domain("emotion_regulation_domain")

    assert domain is not None
    assert "DERS" in domain.suggested_assessment_tools
    assert "emotional_suppression" in domain.fingerprint_dimensions


def test_relationships_domain_uses_ecr_style_tools():
    domain = get_assessment_domain("relationships_domain")

    assert domain is not None
    assert "ECR-R" in domain.suggested_assessment_tools
    assert "attachment_anxiety" in domain.fingerprint_dimensions
    assert "relationship" in domain.semantic_fact_categories
