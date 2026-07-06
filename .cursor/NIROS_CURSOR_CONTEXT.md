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

## NIROS Roadmap Context

**Current priority:**

1. Finish Voice Input pipeline: Voice → Whisper → Transcript → existing text pipeline.
2. Build minimal working UI: Text/Voice input → Human Digital Fingerprint → StrategyCandidate → StrategyExplanation.
3. Add Icaro Generator contract: Strategy → IcaroProfile. Icaro generation must NOT choose therapy; it only expresses an already selected therapeutic strategy.
4. Future Vocal Pattern Engine: Use Maria Sabina chants only as historical source material for extracting psychotherapeutic vocal structures. Do NOT copy chants. Extract functional patterns such as identity reinforcement, acceptance, grounding, permission, closure, transition, protection, symbolic framing.
5. Future Audio Research Engine: Research psilocybin-session music/audio structure, acoustic features, frequency ranges, tempo, repetition, pauses, vocal contour, and therapeutic effects. R&D only, not current MVP.
6. Future Sensor Fusion Engine: Integrate EEG, HRV, heart rate, breathing, EDA/GSR, and subjective feedback. Goal: estimate current therapeutic state and later compare audio/vocal interventions against physiological response.

**Core principle:** Therapeutic strategy is always selected by NIROS core:

Human Digital Fingerprint → Pattern–Person Fit → StrategyCandidate

Delivery modules come AFTER strategy: Text, Voice, Icaro, Audio, Somatic, Sensors.

**Important:** Do not implement Icaro, audio research, or sensors unless explicitly requested.

**Current implementation path:** Voice Input → Whisper Adapter → UI → Icaro Contract.

## Future Patient / Session Storage

NIROS will need a local-first patient/session storage layer.

**Core principle:**

- Do not require personal names.
- Use anonymous numeric patient IDs.
- Each patient has a stable patient number.
- Every intake, transcript, fingerprint, strategy, session, icaro/audio output, and sensor record must be attached to that patient ID.
- Sessions must never float globally without patient linkage.

**Future structure:**

Patient ID → Session ID → Transcript → Human Digital Fingerprint → Pattern–Person Fit Report → StrategyCandidate → StrategyExplanation → optional future outputs (IcaroProfile, AudioProfile, SensorFeedback, SessionOutcome).

**Privacy principle:**

- Prefer pseudonymous IDs over names.
- Names are optional and not required for MVP.
- Storage should support future export/delete per patient.

**Important:** Do not implement database yet unless explicitly requested.

**Current priority remains:** Voice Input → Whisper Adapter → minimal UI → Icaro Contract.