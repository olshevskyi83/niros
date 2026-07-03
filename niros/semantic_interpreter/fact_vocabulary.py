# This vocabulary is the only language LLM providers are allowed to emit.
# NIROS Core owns this vocabulary.
# LLMs must adapt to NIROS.
# NIROS must never adapt its reasoning to a specific LLM.

from __future__ import annotations

SELF = "self"
AGENCY = "agency"
EMOTION = "emotion"
RELATIONSHIP = "relationship"
SAFETY = "safety"
BODY = "body"
SPEECH = "speech"
SESSION = "session"
TRAUMA = "trauma"
MEANING = "meaning"

IDENTITY = "identity"
SELF_EFFICACY = "self_efficacy"
SELF_WORTH = "self_worth"
REACTION_TO_CRITICISM = "reaction_to_criticism"
FEAR_OF_REJECTION = "fear_of_rejection"
BOUNDARY_SETTING = "boundary_setting"
TRUST = "trust"
ATTACHMENT = "attachment"
CONFLICT = "conflict"
REPORTED_FEAR = "reported_fear"
REPORTED_DISTRESS = "reported_distress"
SAFETY_FEELING = "safety_feeling"
PAIN_BURDEN = "pain_burden"
BODY_TRUST = "body_trust"
SPEECH_COMFORT = "speech_comfort"
SESSION_OPENNESS = "session_openness"
TRAUMA_STRESS = "trauma_stress"
MEANING_SENSE = "meaning_sense"
CHANGE_DESIRE = "change_desire"

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
ELEVATED = "elevated"
REDUCED = "reduced"
UNCERTAIN = "uncertain"
SEEKING = "seeking"
RESISTANT = "resistant"
OPEN = "open"
BLOCKED = "blocked"

VALID_CATEGORIES = frozenset(
    {
        SELF,
        AGENCY,
        EMOTION,
        RELATIONSHIP,
        SAFETY,
        BODY,
        SPEECH,
        SESSION,
        TRAUMA,
        MEANING,
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
        REPORTED_FEAR,
        REPORTED_DISTRESS,
        SAFETY_FEELING,
        PAIN_BURDEN,
        BODY_TRUST,
        SPEECH_COMFORT,
        SESSION_OPENNESS,
        TRAUMA_STRESS,
        MEANING_SENSE,
        CHANGE_DESIRE,
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
        ELEVATED,
        REDUCED,
        UNCERTAIN,
        SEEKING,
        RESISTANT,
        OPEN,
        BLOCKED,
    }
)
