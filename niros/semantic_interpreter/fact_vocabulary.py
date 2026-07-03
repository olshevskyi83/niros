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
LIFE_EVENT = "life_event"
SUBSTANCE = "substance"
SOCIAL = "social"
TREATMENT = "treatment"

SLEEP = "sleep"
PSYCHEDELIC = "psychedelic"

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
REPORTED_LOW_MOOD = "reported_low_mood"
CHRONIC_STRESS = "chronic_stress"
REPORTED_FATIGUE = "reported_fatigue"
REPORTED_PAIN = "reported_pain"
PERCEIVED_HELPLESSNESS = "perceived_helplessness"
NIGHTMARES = "nightmares"
STUTTERING = "stuttering"
FEAR_OF_BAD_TRIP = "fear_of_bad_trip"
SAFETY_FEELING = "safety_feeling"
PAIN_BURDEN = "pain_burden"
BODY_TRUST = "body_trust"
SPEECH_COMFORT = "speech_comfort"
SESSION_OPENNESS = "session_openness"
TRAUMA_STRESS = "trauma_stress"
MEANING_SENSE = "meaning_sense"
CHANGE_DESIRE = "change_desire"
BEREAVEMENT = "bereavement"
LOSS = "loss"
GRIEF = "grief"
LOSS_RELATED_DISTRESS = "loss_related_distress"
SEPARATION_DISTRESS = "separation_distress"
BREAKUP = "breakup"
SEPARATION = "separation"
ABANDONMENT = "abandonment"
SUBSTANCE_USE = "substance_use"
DRUG_USE_CONCERN = "drug_use_concern"
ADDICTION_CONCERN = "addiction_concern"
COMPULSIVE_USE = "compulsive_use"
LOSS_OF_CONTROL_USE = "loss_of_control_use"
SUBSTANCE_PREOCCUPATION = "substance_preoccupation"
RECOVERY_GOAL = "recovery_goal"
ACCIDENT = "accident"
TRAUMATIC_EVENT = "traumatic_event"
INSOMNIA = "insomnia"
SLEEP_DISRUPTION = "sleep_disruption"
APPETITE_LOSS = "appetite_loss"
SOCIAL_WITHDRAWAL = "social_withdrawal"
UNWORTHINESS = "unworthiness"
BELONGING = "belonging"
FEELING_UNWANTED = "feeling_unwanted"
CLINICAL_LABEL_SELF_REPORT = "clinical_label_self_report"
MEDICATION_HISTORY = "medication_history"
NEGATIVE_MEDICATION_EXPERIENCE = "negative_medication_experience"
LOW_RESPONSE = "low_response"

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

DEPRESSION = "depression"

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
        LIFE_EVENT,
        SUBSTANCE,
        SOCIAL,
        TREATMENT,
        SLEEP,
        PSYCHEDELIC,
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
        REPORTED_LOW_MOOD,
        CHRONIC_STRESS,
        REPORTED_FATIGUE,
        REPORTED_PAIN,
        PERCEIVED_HELPLESSNESS,
        NIGHTMARES,
        STUTTERING,
        FEAR_OF_BAD_TRIP,
        SAFETY_FEELING,
        PAIN_BURDEN,
        BODY_TRUST,
        SPEECH_COMFORT,
        SESSION_OPENNESS,
        TRAUMA_STRESS,
        MEANING_SENSE,
        CHANGE_DESIRE,
        BEREAVEMENT,
        LOSS,
        GRIEF,
        LOSS_RELATED_DISTRESS,
        SEPARATION_DISTRESS,
        BREAKUP,
        SEPARATION,
        ABANDONMENT,
        SUBSTANCE_USE,
        DRUG_USE_CONCERN,
        ADDICTION_CONCERN,
        COMPULSIVE_USE,
        LOSS_OF_CONTROL_USE,
        SUBSTANCE_PREOCCUPATION,
        RECOVERY_GOAL,
        ACCIDENT,
        TRAUMATIC_EVENT,
        INSOMNIA,
        SLEEP_DISRUPTION,
        APPETITE_LOSS,
        SOCIAL_WITHDRAWAL,
        UNWORTHINESS,
        BELONGING,
        FEELING_UNWANTED,
        CLINICAL_LABEL_SELF_REPORT,
        MEDICATION_HISTORY,
        NEGATIVE_MEDICATION_EXPERIENCE,
        LOW_RESPONSE,
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
        DEPRESSION,
    }
)
