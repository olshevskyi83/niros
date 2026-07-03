from niros.assessment_domain_map import (
    CORE_DOMAIN_IDS,
    FORBIDDEN_DIAGNOSTIC_PHRASES,
    SUGGESTED_ASSESSMENT_TOOLS,
    VALID_FINGERPRINT_DIMENSIONS,
    AssessmentDomain,
    all_assessment_domains,
    build_assessment_domain_map,
    domain_map_contains_diagnostic_language,
    get_assessment_domain,
)
from niros.knowledge import PatternLoader
from niros.semantic_interpreter.fact_vocabulary import VALID_CATEGORIES


def test_all_domain_ids_are_unique():
    domain_map = build_assessment_domain_map()

    assert len(domain_map) == len(set(domain_map))
    assert len(domain_map) == len(CORE_DOMAIN_IDS)


def test_all_twenty_core_domains_exist():
    domain_map = build_assessment_domain_map()

    assert set(domain_map) == set(CORE_DOMAIN_IDS)
    assert len(CORE_DOMAIN_IDS) == 26


def test_every_domain_has_at_least_one_pattern_id():
    for domain in all_assessment_domains():
        assert domain.pattern_ids, f"{domain.domain_id} has no pattern_ids"


def test_every_domain_maps_to_fingerprint_dimensions():
    for domain in all_assessment_domains():
        assert domain.fingerprint_dimensions, f"{domain.domain_id} has no fingerprint_dimensions"
        assert all(
            dimension in VALID_FINGERPRINT_DIMENSIONS for dimension in domain.fingerprint_dimensions
        ), f"{domain.domain_id} uses unknown fingerprint dimension"


def test_every_domain_has_semantic_fact_categories():
    for domain in all_assessment_domains():
        assert domain.semantic_fact_categories, f"{domain.domain_id} has no semantic_fact_categories"
        assert all(
            category in VALID_CATEGORIES for category in domain.semantic_fact_categories
        ), f"{domain.domain_id} uses unknown semantic category"


def test_no_domain_uses_diagnostic_language():
    for domain in all_assessment_domains():
        assert not domain_map_contains_diagnostic_language(domain), (
            f"{domain.domain_id} contains forbidden diagnostic language"
        )


def test_map_is_deterministic():
    first = build_assessment_domain_map()
    second = build_assessment_domain_map()

    assert first == second
    assert all(first[domain_id] == get_assessment_domain(domain_id) for domain_id in CORE_DOMAIN_IDS)


def test_all_pattern_ids_exist_in_knowledge_base():
    known_patterns = frozenset(pattern.canonical_id for pattern in PatternLoader().load_all())

    for domain in all_assessment_domains():
        missing = [pattern_id for pattern_id in domain.pattern_ids if pattern_id not in known_patterns]
        assert not missing, f"{domain.domain_id} references unknown patterns: {missing}"


def test_suggested_assessment_tools_use_known_catalog():
    for domain in all_assessment_domains():
        unknown = [
            tool for tool in domain.suggested_assessment_tools if tool not in SUGGESTED_ASSESSMENT_TOOLS
        ]
        assert not unknown, f"{domain.domain_id} references unknown tools: {unknown}"


def test_grief_domain_covers_new_loss_patterns():
    domain = get_assessment_domain("grief_loss_bereavement")

    assert domain is not None
    assert "bereavement_context" in domain.pattern_ids
    assert "loss_related_distress" in domain.pattern_ids
    assert "grief_signal" in domain.pattern_ids
    assert "life_event" in domain.semantic_fact_categories


def test_psychedelic_session_concerns_has_highest_priority():
    domain_map = build_assessment_domain_map()
    psychedelic = domain_map["psychedelic_session_concerns"]
    priorities = [domain.priority for domain in domain_map.values()]

    assert psychedelic.priority == max(priorities)


def test_assessment_domain_is_frozen_dataclass():
    domain = all_assessment_domains()[0]

    assert isinstance(domain, AssessmentDomain)
    assert FORBIDDEN_DIAGNOSTIC_PHRASES
