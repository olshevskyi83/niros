# Future Input Pipeline

This document describes the planned input architecture for NIROS text, voice, and facilitator modes. It is design documentation only. Nothing in this document changes the current MVP runtime.

## Current MVP: Text Mode

```
Text
  ↓
OpenAI Semantic Interpreter
  ↓
Human Language Understanding
  ↓
Psychological Signal Graph
  ↓
Human Digital Fingerprint
```

## Future Voice Mode

```
Voice
  ↓
Speech-to-Text Layer
  ↓
Transcript Review / Confirmation
  ↓
OpenAI Semantic Interpreter
  ↓
Human Language Understanding
  ↓
Psychological Signal Graph
  ↓
Human Digital Fingerprint
```

## Future Facilitator Mode

```
Human speaks
  ↓
Facilitator writes transcript or summary
  ↓
OpenAI Semantic Interpreter
  ↓
Human Language Understanding
  ↓
Psychological Signal Graph
  ↓
Human Digital Fingerprint
```

## Responsibilities

### Speech-to-Text Layer

Speech recognition only.

Possible implementations:

- Whisper
- Faster-Whisper
- Apple Speech
- Vosk
- Deepgram
- Azure Speech

### OpenAI

Semantic interpretation only.

### NIROS

Psychological reasoning only.

## Design Principle

Voice is transcribed first.

Text is semantically interpreted second.

NIROS reasons third.

Speech recognition should be replaceable without changing the psychological pipeline.

Transcript review is important because incorrect transcription can change psychological meaning.

Example:

`я не хочу жити так`

is not the same as

`я не хочу жити`

The system should allow transcript confirmation before psychological processing when voice mode is used.
