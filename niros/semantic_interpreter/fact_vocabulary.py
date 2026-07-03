# This vocabulary is the only language LLM providers are allowed to emit.
# NIROS Core owns this vocabulary.
# LLMs must adapt to NIROS.
# NIROS must never adapt its reasoning to a specific LLM.

from __future__ import annotations

SELF = "self"
AGENCY = "agency"
EMOTION = "emotion"
RELATIONSHIP = "relationship"

IDENTITY = "identity"
SELF_EFFICACY = "self_efficacy"
SELF_WORTH = "self_worth"
REACTION_TO_CRITICISM = "reaction_to_criticism"
FEAR_OF_REJECTION = "fear_of_rejection"
BOUNDARY_SETTING = "boundary_setting"
TRUST = "trust"
ATTACHMENT = "attachment"
CONFLICT = "conflict"

UNCLEAR = "unclear"
LOW = "low"
HIGH = "high"
STRONG = "strong"
WEAK = "weak"
STABLE = "stable"
UNSTABLE = "unstable"
PRESENT = "present"
ABSENT = "absent"
AVOIDANT = "avoidant"
ANXIOUS = "anxious"

VALID_CATEGORIES = frozenset(
    {
        SELF,
        AGENCY,
        EMOTION,
        RELATIONSHIP,
    }
)

VALID_ATTRIBUTES = frozenset(
    {
        IDENTITY,
        SELF_EFFICACY,
        SELF_WORTH,
        REACTION_TO_CRITICISM,
        FEAR_OF_REJECTION,
        BOUNDARY_SETTING,
        TRUST,
        ATTACHMENT,
        CONFLICT,
    }
)

VALID_VALUES = frozenset(
    {
        UNCLEAR,
        LOW,
        HIGH,
        STRONG,
        WEAK,
        STABLE,
        UNSTABLE,
        PRESENT,
        ABSENT,
        AVOIDANT,
        ANXIOUS,
    }
)
