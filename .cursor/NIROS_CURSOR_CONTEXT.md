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

**Current path — Adaptive Intake Brain:**

Coverage → Clarification → Conversational Intake → Strategy

Finish this before Research Intake Assistant or other expansion work.

**Completed or in progress (do not re-open without reason):**

Voice Input contracts, Whisper Adapter (mock), Minimal UI, Patient Repository, Pattern–Person Fit, StrategyCandidate, Intake Coverage, Clarification Selector.

**Later:**

Icaro Generator Contract, Audio/Icaro R&D, Sensor Fusion, Research Intake Assistant.

## NIROS Strategic Lock

NIROS is not an endless module project.

Every new feature must answer at least one of these questions:

1. Does it improve Knowledge?
2. Does it improve Reasoning?
3. Does it improve Personalization for a specific person?
4. Does it move the project closer to a working MVP?

If not, do not implement it.

## Knowledge Growth Strategy

NIROS must not depend on thousands of patients to become useful.

Primary knowledge growth comes from:

- psychotherapy manuals
- clinical protocols
- systematic reviews
- meta-analyses
- psilocybin therapy studies
- music and psychedelic therapy studies
- neuroscience papers
- Maria Sabina / traditional chant material as structural source
- carefully reviewed human experience notes

All external knowledge must pass through TLE:

Source → Corpus Registry → Knowledge Chunks → Meaning Units → Candidate Therapeutic Mechanisms → Similarity / Consolidation → Human Review → Universal Pattern Library

OpenAI may assist with:

- semantic interpretation
- summarization
- source triage
- question wording
- extraction assistance

OpenAI must NOT:

- silently create global therapeutic rules
- overwrite NIROS reasoning
- decide therapy independently
- add unverified knowledge directly into Universal Pattern Library

## Learning Strategy

NIROS learning has three layers:

1. **Global Knowledge**
   - grows mostly from literature and reviewed sources
   - changes slowly
   - never changes automatically from one user

2. **Reasoning Layer**
   - deterministic and explainable
   - includes Coverage Engine, Clarification Engine, Pattern–Person Fit, StrategyCandidate
   - updated only through deliberate code/version changes

3. **Patient Personalization**
   - grows quickly per patient
   - remembers what worked for PT-xxxxx
   - does not rewrite global rules automatically

## Small-Data Principle

NIROS must work even with 1–20 users.

It should learn within a patient over sessions:

- which questions increase coverage
- which strategies are useful
- which delivery modes are tolerated
- which patterns should be repeated or avoided

Large datasets are useful but not required for MVP.

## Research Intake Future

Future feature: **Research Intake Assistant**.

Purpose: help find, register, and triage new scientific sources.

Rules:

- must store source title, authors, year, DOI/URL if available
- must mark source type: trial, review, manual, transcript, chant, neuroscience, music, other
- must not inject knowledge directly into production library
- everything goes through TLE and Human Review

Do not implement Research Intake Assistant yet unless explicitly requested.