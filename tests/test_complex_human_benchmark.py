"""Validate the complex synthetic human benchmark corpus."""

from __future__ import annotations

from pathlib import Path

from niros.knowledge import PatternLoader

from test_human_cases import load_bullet_section, load_scenario_text

COMPLEX_CASES_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "test_cases" / "complex"

REQUIRED_SECTIONS = (
    "Expected Patterns",
    "Expected Weak Domains",
    "Expected Assessments",
    "Expected Strategy Focus",
    "Expected Scenario Themes",
    "Expected Timeline Characteristics",
)

SCENARIO_SECTIONS = (
    "Background",
    "Current Life",
    "Thoughts",
    "Emotions",
    "Relationships",
    "Goals",
    "Values",
    "Internal Conflicts",
)


def _case_paths() -> list[Path]:
    return sorted(COMPLEX_CASES_DIR.glob("c*.md"))


def test_complex_benchmark_has_at_least_thirty_cases():
    cases = _case_paths()
    assert len(cases) >= 30


def test_complex_cases_have_required_metadata_sections():
    for case_path in _case_paths():
        for section in REQUIRED_SECTIONS:
            items = load_bullet_section(case_path, section)
            assert items, f"{case_path.name} missing {section}"


def test_complex_cases_have_interview_structure_and_word_count():
    for case_path in _case_paths():
        scenario = load_scenario_text(case_path)
        word_count = len(scenario.split())
        assert 500 <= word_count <= 1500, f"{case_path.name} has {word_count} words"
        lowered = scenario.lower()
        for section in SCENARIO_SECTIONS:
            assert section.lower() in lowered, f"{case_path.name} missing {section} section"


def test_complex_cases_reference_known_patterns():
    known = frozenset(p.canonical_id for p in PatternLoader().load_all())
    for case_path in _case_paths():
        patterns = load_bullet_section(case_path, "Expected Patterns")
        missing = [pattern_id for pattern_id in patterns if pattern_id not in known]
        assert not missing, f"{case_path.name} unknown patterns: {missing}"
