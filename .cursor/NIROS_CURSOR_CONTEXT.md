# NIROS Cursor Context

You are working inside NIROS Research OS v4 Foundation Release.

## Read first

1. `README.md`
2. `00_SYSTEM_MAP.md`
3. `00_NIROS_ROADMAP.md`
4. `01_Vision/01_NIROS_Design_Principles.md`
5. `04_Human_Understanding_Engine/00_HUE_Overview.md`
6. `16_Development/01_Cursor_Workflow.md`

## Architecture freeze

Do not rename top-level folders. Do not invent new top-level modules unless the user explicitly asks and an ADR is created.

## First implementation target

Human Understanding Engine MVP:

- text-based interview
- explicit state machine
- question library
- structured extraction
- risk screen
- declared vs confirmed problem logic
- final HumanProfile JSON



## Safety rules

- No diagnosis claims.
- No autonomous medical instruction.
- Risk checks interrupt normal flow.
- Sensor data is supportive only.
- All important outputs should be explainable.



## Coding style

- Prefer small modules.
- Prefer typed data models / schemas.
- Add tests for every state transition.
- Add schema validation for AI outputs.
- Keep prompt contracts in versioned files.



## Multilingual Architecture Decision

NIROS separates three language layers:

1. Interview Language

   - Language used by the user during the interview.

   - MVP supported languages:

     - English: en

     - Spanish: es

     - Russian: ru

   - The agent should respond in the same language as the user input.

2. Internal Canonical Representation

   - Internal psychological logic must be language-independent.

   - Concepts, evidence, hypotheses, traits, and tags must use stable canonical IDs.

   - Example:

     - fear_of_rejection

     - not "страх отвержения"

     - not "miedo al rechazo"

3. Output / Ceremony Language

   - Reports may be generated in the user's selected language.

   - Icaros / ceremonial output is separate from interview language.

   - Future supported icaro languages:

     - Spanish: es

     - Quechua: qu

     - Shipibo: shipibo

     - Mazatec: mazatec

Rule:

Interview language and icaro language must not be tightly coupled.

A user may complete the interview in English, Spanish, or Russian, while ceremonial output may be generated separately in Spanish, Quechua, Shipibo, or Mazatec.

Future languages may be added without changing the internal canonical representation.

All psychological reasoning must operate on canonical IDs, never on translated text.

## Future Patient / Session Storage

NIROS will need a local-first patient/session storage layer.

**Core principles:**

- Use anonymous numeric patient IDs.
- Names are optional and not required for MVP.
- Every intake, transcript, fingerprint, strategy, session, Icaro/audio output, sensor record, and outcome must be attached to a `patient_id`.
- No session data should exist without patient linkage.

**Future hierarchy:**

Patient ID → Session ID → Transcript → Human Digital Fingerprint → Pattern–Person Fit Report → StrategyCandidate → StrategyExplanation → optional future outputs (IcaroProfile, AudioProfile, SensorFeedback, SessionOutcome).

**Privacy:**

- Prefer pseudonymous IDs over names.
- Support future export/delete per patient.
- Core NIROS should work without personal names.

## Future Fingerprint History

Human Digital Fingerprint should eventually support history, not only one static profile.

**Future model:** Patient ID → Fingerprint v1 → Fingerprint v2 → Fingerprint v3

**Purpose:** track changes over time in signals such as self_criticism, emotional_avoidance, shame_sensitivity, agency, meaning, emotional_flexibility.

## Future Stable vs Dynamic Model

Future NIROS should separate:

**Stable Fingerprint:** personality traits, values, long-term patterns, identity structure, attachment style, baseline worldview.

**Dynamic Therapeutic State:** current anxiety, current shame, overwhelm risk, readiness for deep work, emotional stability, current physiological state, possible future neuroplasticity window.

## Future Sensor Fusion Engine

Future sensor layer may include: EEG, HRV, heart rate, breathing, EDA/GSR, voice features, subjective report.

**Goal:** estimate Current Therapeutic State and compare interventions against physiological response.

**Future loop:** Patient ID → Stable Fingerprint → Current Therapeutic State → Pattern–Person Fit → Strategy → Icaro / Audio / Text Delivery → Sensor Feedback → Updated Therapeutic State.

## Future NeuroAudio Research Engine

Future R&D module only, not current MVP.

**Purpose:** analyze psilocybin-session music/audio, Maria Sabina vocal recordings, acoustic features, vocal contour, tempo, repetition, pauses, frequency ranges, and later physiological feedback.

**Goal:** derive reusable audio/vocal templates for therapeutic delivery.

**Important:** This must not choose therapy. Therapeutic strategy is selected only by NIROS core:

Human Digital Fingerprint → Pattern–Person Fit → StrategyCandidate

Audio, Icaro, sensors, and UI are delivery or feedback layers AFTER strategy.

## Current Implementation Priority

Do not implement future modules unless explicitly requested.

**Current path:**

1. Voice Input contracts
2. Whisper Adapter
3. Minimal UI
4. Icaro Generator Contract
5. Later: Patient Repository
6. Later: Audio/Icaro R&D
7. Later: Sensor Fusion