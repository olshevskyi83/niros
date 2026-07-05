"""Spirituality / Worldview — first-class Human Digital Fingerprint domain.

Descriptive only: adapts symbolic language and session framing; never judges the person.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from niros.assessment import AssessmentResult
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    COVERAGE_LEVEL_GOOD,
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
)
from niros.patterns import PatternTag
from niros.semantic_interpreter.facts import SemanticFact

SPIRITUALITY_WORLDVIEW_DOMAIN = "spirituality_worldview"

ORIENTATION_UNKNOWN = "unknown"
ORIENTATION_ATHEIST = "atheist"
ORIENTATION_SECULAR_HUMANIST = "secular_humanist"
ORIENTATION_AGNOSTIC = "agnostic"
ORIENTATION_SPIRITUAL_NOT_RELIGIOUS = "spiritual_not_religious"
ORIENTATION_CHRISTIAN = "christian"
ORIENTATION_RELIGIOUS_OTHER = "religious_other"
ORIENTATION_NATURE_SPIRITUAL = "nature_spiritual"
ORIENTATION_RELIGION_AVERSE = "religion_averse"
ORIENTATION_SYMBOLIC_OPEN = "symbolic_open"
ORIENTATION_SKEPTICAL_OPEN = "skeptical_open"

OPENNESS_UNKNOWN = "unknown"
OPENNESS_LOW = "low"
OPENNESS_MEDIUM = "medium"
OPENNESS_HIGH = "high"

COMFORT_UNKNOWN = "unknown"
COMFORT_AVOID = "avoid"
COMFORT_CAUTIOUS = "cautious"
COMFORT_ALLOWED = "allowed"
COMFORT_PREFERRED = "preferred"

SPIRITUAL_PATTERN_IDS = frozenset(
    {
        "spiritual_openness",
        "spiritual_resistance",
        "meaning_seeking",
        "mystical_expectation",
        "desire_for_change",
        "search_for_self_understanding",
    }
)

TEXT_ORIENTATION_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("do not believe in god", "don't believe in god", "i am an atheist", "i'm an atheist"), ORIENTATION_ATHEIST),
    (("prefer secular", "secular, psychological language", "secular psychological language"), ORIENTATION_SECULAR_HUMANIST),
    (("do not know what i believe", "don't know what i believe", "not sure about spirituality", "i am not sure about spirituality"), ORIENTATION_AGNOSTIC),
    (("holy trinity", "christian faith", "believe in god, jesus", "believe in god and jesus", "my christian faith", "i am christian", "i'm christian"), ORIENTATION_CHRISTIAN),
    (("religious language makes me uncomfortable", "do not want prayer", "don't want prayer", "no god language", "god language"), ORIENTATION_RELIGION_AVERSE),
    (("not religious, but i feel connected", "not religious but i feel connected", "connected to something bigger"), ORIENTATION_SPIRITUAL_NOT_RELIGIOUS),
    (("connected through nature", "forests, rivers, mountains", "feel connected through nature"), ORIENTATION_NATURE_SPIRITUAL),
    (("skeptical, but i am open", "skeptical but open", "skeptical, but open"), ORIENTATION_SKEPTICAL_OPEN),
    (("symbols and myths can move me", "symbolic or poetic language", "myths can move me"), ORIENTATION_SYMBOLIC_OPEN),
)

SYMBOLIC_PREFERENCE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "nature": ("nature", "forest", "river", "mountain", "plant"),
    "body": ("body", "embodied", "somatic"),
    "breath": ("breath", "breathing"),
    "light": ("light", "illumination"),
    "ancestors": ("ancestor", "ancestral"),
    "prayer": ("prayer", "pray"),
    "god": (" god", "god "),
    "christ": ("christ", "jesus"),
    "holy_spirit": ("holy spirit",),
    "inner_wisdom": ("inner wisdom", "inner knowing"),
    "science": ("science", "scientific"),
    "humanism": ("humanist", "humanism"),
}

AVOIDED_SYMBOL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "god": ("god language", " believe in god", "don't believe in god", "do not believe in god"),
    "prayer": ("prayer", "pray"),
    "angels": ("angel",),
    "salvation": ("salvation",),
    "spirits": ("spirit", "spirits"),
    "ancestors": ("ancestor",),
    "religion": ("religious language", "religion"),
    "supernatural_claims": ("supernatural", "literal claims"),
}


@dataclass(frozen=True)
class SpiritualityWorldviewProfile:
    worldview_orientation: str = ORIENTATION_UNKNOWN
    spiritual_openness: str = OPENNESS_UNKNOWN
    religious_language_comfort: str = COMFORT_UNKNOWN
    symbolic_language_preferences: tuple[str, ...] = ()
    avoided_symbolic_language: tuple[str, ...] = ()
    icaros_language_constraints: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, str | tuple[str, ...]]:
        return {
            "worldview_orientation": self.worldview_orientation,
            "spiritual_openness": self.spiritual_openness,
            "religious_language_comfort": self.religious_language_comfort,
            "symbolic_language_preferences": self.symbolic_language_preferences,
            "avoided_symbolic_language": self.avoided_symbolic_language,
            "icaros_language_constraints": self.icaros_language_constraints,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SpiritualityWorldviewProfile:
        return cls(
            worldview_orientation=str(payload.get("worldview_orientation", ORIENTATION_UNKNOWN)),
            spiritual_openness=str(payload.get("spiritual_openness", OPENNESS_UNKNOWN)),
            religious_language_comfort=str(payload.get("religious_language_comfort", COMFORT_UNKNOWN)),
            symbolic_language_preferences=tuple(payload.get("symbolic_language_preferences", ())),
            avoided_symbolic_language=tuple(payload.get("avoided_symbolic_language", ())),
            icaros_language_constraints=tuple(payload.get("icaros_language_constraints", ())),
        )

    def completeness_score(self) -> float:
        score = 0.0
        if self.worldview_orientation != ORIENTATION_UNKNOWN:
            score += 0.35
        if self.spiritual_openness != OPENNESS_UNKNOWN:
            score += 0.15
        if self.religious_language_comfort != COMFORT_UNKNOWN:
            score += 0.20
        if self.symbolic_language_preferences:
            score += 0.15
        if self.avoided_symbolic_language:
            score += 0.10
        if self.icaros_language_constraints:
            score += 0.05
        return min(1.0, score)

    def coverage_level(self) -> str:
        score = self.completeness_score()
        if score >= 0.90:
            return COVERAGE_LEVEL_COMPLETE
        if score >= 0.50:
            return COVERAGE_LEVEL_GOOD
        if score >= 0.25:
            return COVERAGE_LEVEL_PARTIAL
        return COVERAGE_LEVEL_UNKNOWN


def extract_worldview_signals_from_text(text: str) -> list[SemanticFact]:
    lowered = " ".join(text.lower().split())
    if not lowered:
        return []

    facts: list[SemanticFact] = []
    orientation = _orientation_from_text(lowered)
    if orientation != ORIENTATION_UNKNOWN:
        facts.append(
            SemanticFact(
                category="meaning",
                attribute="worldview_orientation",
                value=orientation,
                evidence=text.strip()[:240],
            )
        )

    for symbol, keywords in SYMBOLIC_PREFERENCE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            facts.append(
                SemanticFact(
                    category="meaning",
                    attribute="symbolic_language_preference",
                    value=symbol,
                    evidence=text.strip()[:240],
                )
            )

    for symbol, keywords in AVOIDED_SYMBOL_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            facts.append(
                SemanticFact(
                    category="meaning",
                    attribute="avoided_symbolic_language",
                    value=symbol,
                    evidence=text.strip()[:240],
                )
            )

    if "religious language" in lowered and any(token in lowered for token in ("uncomfortable", "avoid", "does not work")):
        facts.append(
            SemanticFact(
                category="session",
                attribute="religious_language_comfort",
                value=COMFORT_AVOID,
                evidence=text.strip()[:240],
            )
        )
    elif orientation == ORIENTATION_CHRISTIAN:
        facts.append(
            SemanticFact(
                category="session",
                attribute="religious_language_comfort",
                value=COMFORT_ALLOWED,
                evidence=text.strip()[:240],
            )
        )

    openness = _openness_from_text_and_orientation(lowered, orientation)
    if openness != OPENNESS_UNKNOWN:
        facts.append(
            SemanticFact(
                category="session",
                attribute="spiritual_openness",
                value=openness,
                evidence=text.strip()[:240],
            )
        )

    return facts


def build_spirituality_worldview_profile(
    *,
    presenting_problem: dict[str, str] | None = None,
    pattern_ids: Iterable[str] | None = None,
    semantic_facts: Iterable[SemanticFact] | None = None,
    matched_texts: Iterable[str] | None = None,
    assessment_results: Iterable[AssessmentResult] | None = None,
) -> SpiritualityWorldviewProfile:
    patterns = set(pattern_ids or ())
    facts = list(semantic_facts or [])
    combined_text = _combined_source_text(presenting_problem, matched_texts)
    fact_evidence = " ".join(
        fact.evidence.strip()
        for fact in facts
        if fact.evidence and fact.evidence.strip()
    )
    if fact_evidence:
        combined_text = f"{combined_text} {fact_evidence}".strip()
    extracted_facts = extract_worldview_signals_from_text(combined_text)
    merged_facts = _merge_facts(facts + extracted_facts)

    orientation = _orientation_from_facts_and_patterns(merged_facts, patterns, combined_text)
    openness = _openness_from_facts_patterns(merged_facts, patterns, orientation)
    comfort = _comfort_from_facts_patterns(merged_facts, patterns, orientation)
    preferences = _preferences_from_facts_patterns(merged_facts, patterns, combined_text, orientation)
    avoided = _avoided_from_facts_patterns(merged_facts, combined_text, orientation, comfort)
    constraints = _icaros_constraints(orientation, comfort, openness, preferences, avoided)

    orientation, openness, comfort, preferences, avoided, constraints = _apply_assessment_results(
        orientation,
        openness,
        comfort,
        preferences,
        avoided,
        constraints,
        assessment_results,
    )

    return SpiritualityWorldviewProfile(
        worldview_orientation=orientation,
        spiritual_openness=openness,
        religious_language_comfort=comfort,
        symbolic_language_preferences=tuple(dict.fromkeys(preferences)),
        avoided_symbolic_language=tuple(dict.fromkeys(avoided)),
        icaros_language_constraints=tuple(dict.fromkeys(constraints)),
    )


def worldview_coverage_value(profile: SpiritualityWorldviewProfile) -> float:
    return profile.completeness_score()


def render_worldview_profile_section(profile: SpiritualityWorldviewProfile) -> str:
    lines = [
        f"- Worldview orientation: {profile.worldview_orientation.replace('_', ' ')}",
        f"- Spiritual openness: {profile.spiritual_openness}",
        f"- Religious language comfort: {profile.religious_language_comfort}",
    ]
    if profile.symbolic_language_preferences:
        lines.append(
            "- Preferred symbolic language: "
            + ", ".join(profile.symbolic_language_preferences)
        )
    else:
        lines.append("- Preferred symbolic language: not yet clear")

    if profile.avoided_symbolic_language:
        lines.append(
            "- Avoided symbolic language: "
            + ", ".join(profile.avoided_symbolic_language)
        )
    else:
        lines.append("- Avoided symbolic language: none noted yet")

    if profile.icaros_language_constraints:
        lines.append("- Future Icaro language constraints:")
        lines.extend(f"  - {item}" for item in profile.icaros_language_constraints)
    else:
        lines.append("- Future Icaro language constraints: use conservative symbolic language")

    return "\n".join(lines)


def _combined_source_text(
    presenting_problem: dict[str, str] | None,
    matched_texts: Iterable[str] | None,
) -> str:
    chunks: list[str] = []
    if presenting_problem:
        chunks.extend(str(value) for value in presenting_problem.values() if str(value).strip())
    if matched_texts:
        chunks.extend(str(text) for text in matched_texts if str(text).strip())
    return " ".join(chunks)


def _merge_facts(facts: list[SemanticFact]) -> list[SemanticFact]:
    seen: set[tuple[str, str, str]] = set()
    merged: list[SemanticFact] = []
    for fact in facts:
        if not fact.is_valid():
            continue
        key = (fact.category, fact.attribute, fact.value)
        if key in seen:
            continue
        seen.add(key)
        merged.append(fact)
    return merged


def _orientation_from_text(text: str) -> str:
    for phrases, orientation in TEXT_ORIENTATION_RULES:
        if any(phrase in text for phrase in phrases):
            return orientation
    return ORIENTATION_UNKNOWN


def _orientation_from_facts_and_patterns(
    facts: list[SemanticFact],
    patterns: set[str],
    text: str,
) -> str:
    for fact in facts:
        if fact.attribute == "worldview_orientation" and fact.value != ORIENTATION_UNKNOWN:
            return fact.value

    text_orientation = _orientation_from_text(text.lower())
    if text_orientation != ORIENTATION_UNKNOWN:
        return text_orientation

    if "spiritual_resistance" in patterns:
        return ORIENTATION_RELIGION_AVERSE
    if patterns & {"spiritual_openness", "meaning_seeking", "mystical_expectation"}:
        return ORIENTATION_SPIRITUAL_NOT_RELIGIOUS

    return ORIENTATION_UNKNOWN


def _openness_from_text_and_orientation(text: str, orientation: str) -> str:
    if orientation in {ORIENTATION_RELIGION_AVERSE, ORIENTATION_ATHEIST, ORIENTATION_SECULAR_HUMANIST}:
        return OPENNESS_LOW
    if orientation in {ORIENTATION_CHRISTIAN, ORIENTATION_NATURE_SPIRITUAL, ORIENTATION_SPIRITUAL_NOT_RELIGIOUS}:
        return OPENNESS_HIGH
    if orientation in {ORIENTATION_AGNOSTIC, ORIENTATION_SKEPTICAL_OPEN, ORIENTATION_SYMBOLIC_OPEN}:
        return OPENNESS_MEDIUM
    if any(token in text for token in ("open to spiritual", "open to symbolic", "spiritual experience")):
        return OPENNESS_HIGH
    if "resistant" in text or "blocked" in text:
        return OPENNESS_LOW
    return OPENNESS_UNKNOWN


def _openness_from_facts_patterns(
    facts: list[SemanticFact],
    patterns: set[str],
    orientation: str,
) -> str:
    for fact in facts:
        if fact.attribute == "spiritual_openness":
            return fact.value
        if fact.attribute == "session_openness":
            if fact.value in {"open", "seeking"}:
                return OPENNESS_HIGH
            if fact.value in {"resistant", "blocked"}:
                return OPENNESS_LOW

    if "spiritual_openness" in patterns or "meaning_seeking" in patterns:
        return OPENNESS_HIGH
    if "spiritual_resistance" in patterns:
        return OPENNESS_LOW

    text_openness = _openness_from_text_and_orientation("", orientation)
    return text_openness


def _comfort_from_facts_patterns(
    facts: list[SemanticFact],
    patterns: set[str],
    orientation: str,
) -> str:
    for fact in facts:
        if fact.attribute == "religious_language_comfort":
            return fact.value

    if orientation in {ORIENTATION_ATHEIST, ORIENTATION_SECULAR_HUMANIST, ORIENTATION_RELIGION_AVERSE}:
        return COMFORT_AVOID
    if orientation == ORIENTATION_CHRISTIAN:
        return COMFORT_ALLOWED
    if orientation in {ORIENTATION_AGNOSTIC, ORIENTATION_SKEPTICAL_OPEN}:
        return COMFORT_CAUTIOUS
    if orientation in {ORIENTATION_SPIRITUAL_NOT_RELIGIOUS, ORIENTATION_NATURE_SPIRITUAL, ORIENTATION_SYMBOLIC_OPEN}:
        return COMFORT_ALLOWED
    if "spiritual_resistance" in patterns:
        return COMFORT_AVOID
    if patterns & SPIRITUAL_PATTERN_IDS:
        return COMFORT_CAUTIOUS
    return COMFORT_UNKNOWN


def _preferences_from_facts_patterns(
    facts: list[SemanticFact],
    patterns: set[str],
    text: str,
    orientation: str,
) -> list[str]:
    preferences: list[str] = []
    for fact in facts:
        if fact.attribute == "symbolic_language_preference":
            preferences.append(fact.value)

    lowered = text.lower()
    for symbol, keywords in SYMBOLIC_PREFERENCE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            preferences.append(symbol)

    if orientation == ORIENTATION_NATURE_SPIRITUAL and "nature" not in preferences:
        preferences.append("nature")
    if orientation == ORIENTATION_CHRISTIAN:
        for item in ("god", "christ", "light"):
            if item not in preferences:
                preferences.append(item)
    if orientation in {ORIENTATION_SPIRITUAL_NOT_RELIGIOUS, ORIENTATION_SYMBOLIC_OPEN}:
        for item in ("nature", "light", "inner_wisdom"):
            if item not in preferences:
                preferences.append(item)
    if orientation in {ORIENTATION_ATHEIST, ORIENTATION_SECULAR_HUMANIST}:
        for item in ("science", "humanism"):
            if item not in preferences:
                preferences.append(item)
    if "meaning_seeking" in patterns and "inner_wisdom" not in preferences:
        preferences.append("inner_wisdom")
    return preferences


def _avoided_from_facts_patterns(
    facts: list[SemanticFact],
    text: str,
    orientation: str,
    comfort: str,
) -> list[str]:
    avoided: list[str] = []
    for fact in facts:
        if fact.attribute == "avoided_symbolic_language":
            avoided.append(fact.value)

    lowered = text.lower()
    for symbol, keywords in AVOIDED_SYMBOL_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            avoided.append(symbol)

    if orientation in {ORIENTATION_ATHEIST, ORIENTATION_SECULAR_HUMANIST, ORIENTATION_RELIGION_AVERSE}:
        for item in ("god", "prayer", "religion", "supernatural_claims"):
            if item not in avoided:
                avoided.append(item)
    if comfort == COMFORT_AVOID and "religion" not in avoided:
        avoided.append("religion")
    return avoided


def _icaros_constraints(
    orientation: str,
    comfort: str,
    openness: str,
    preferences: list[str],
    avoided: list[str],
) -> list[str]:
    constraints: list[str] = []
    if orientation in {ORIENTATION_ATHEIST, ORIENTATION_SECULAR_HUMANIST}:
        constraints.append("use secular language")
        constraints.append("avoid religious claims")
    if orientation == ORIENTATION_AGNOSTIC:
        constraints.append("avoid certainty about divine beings")
    if orientation == ORIENTATION_RELIGION_AVERSE or comfort == COMFORT_AVOID:
        constraints.append("avoid religious framing")
    if orientation == ORIENTATION_CHRISTIAN and comfort in {COMFORT_ALLOWED, COMFORT_PREFERRED}:
        constraints.append("use Christian-compatible language only when explicitly accepted")
    if orientation in {ORIENTATION_SPIRITUAL_NOT_RELIGIOUS, ORIENTATION_NATURE_SPIRITUAL}:
        constraints.append("use nature metaphors")
    if orientation in {ORIENTATION_SYMBOLIC_OPEN, ORIENTATION_SKEPTICAL_OPEN}:
        constraints.append("use symbolic language without literal claims")
    if openness == OPENNESS_LOW:
        constraints.append("keep symbolic language conservative")
    if "god" in avoided or "religion" in avoided:
        constraints.append("avoid god and religion language")
    if not constraints and orientation == ORIENTATION_UNKNOWN:
        constraints.append("use conservative symbolic language")
    return constraints


def _apply_assessment_results(
    orientation: str,
    openness: str,
    comfort: str,
    preferences: list[str],
    avoided: list[str],
    constraints: list[str],
    assessment_results: Iterable[AssessmentResult] | None,
) -> tuple[str, str, str, list[str], list[str], list[str]]:
    if not assessment_results:
        return orientation, openness, comfort, preferences, avoided, constraints

    for result in assessment_results:
        if result.fingerprint_dimension != SPIRITUALITY_WORLDVIEW_DOMAIN:
            continue
        domain = result.domain_id
        if domain == "worldview_orientation_signal" and result.normalized_score >= 0.5:
            if orientation == ORIENTATION_UNKNOWN:
                orientation = ORIENTATION_SPIRITUAL_NOT_RELIGIOUS
        if domain == "religious_language_avoidance" and result.normalized_score >= 0.6:
            comfort = COMFORT_AVOID
            if "religion" not in avoided:
                avoided.append("religion")
        if domain == "religious_language_preference" and result.normalized_score >= 0.6:
            comfort = COMFORT_PREFERRED
        if domain == "symbolic_openness_signal" and result.normalized_score >= 0.5:
            openness = OPENNESS_HIGH
            if "inner_wisdom" not in preferences:
                preferences.append("inner_wisdom")
        if domain == "nature_symbolic_preference" and result.normalized_score >= 0.5:
            if "nature" not in preferences:
                preferences.append("nature")
        if domain == "secular_framing_preference" and result.normalized_score >= 0.6:
            if orientation == ORIENTATION_UNKNOWN:
                orientation = ORIENTATION_SECULAR_HUMANIST
            comfort = COMFORT_AVOID
            for item in ("god", "prayer", "religion"):
                if item not in avoided:
                    avoided.append(item)
        if domain == "symbolic_preference_consent_waiver" and result.normalized_score <= 0.4:
            if comfort == COMFORT_UNKNOWN:
                comfort = COMFORT_CAUTIOUS
            if "check symbolic language preferences before use" not in constraints:
                constraints.append("check symbolic language preferences before use")

    updated_constraints = list(dict.fromkeys(constraints + _icaros_constraints(
        orientation, comfort, openness, preferences, avoided
    )))
    return orientation, openness, comfort, preferences, avoided, updated_constraints


def pattern_ids_from_tags(detected_patterns: list[PatternTag] | list[str]) -> set[str]:
    if not detected_patterns:
        return set()
    if isinstance(detected_patterns[0], PatternTag):
        return {tag.canonical_id for tag in detected_patterns}  # type: ignore[arg-type]
    return set(str(item) for item in detected_patterns)


def matched_texts_from_tags(detected_patterns: list[PatternTag]) -> list[str]:
    return [tag.matched_text for tag in detected_patterns if tag.matched_text.strip()]
