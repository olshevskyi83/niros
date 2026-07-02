---
type: module-spec
version: v2.0
status: active
tags: [timeline, session-engine, physiology, niros]
---

# Timeline Engine v2

## Purpose

The Timeline Engine synchronizes session events, facilitator actions, voice/script phases, music changes, physiology, and participant responses.

## Why this matters

For NIROS, the most valuable research data may not be raw EEG alone, but the synchronized relationship between:

- what happened in the session;
- what was spoken;
- what music changed;
- what physiological signals changed;
- what the participant later reported.

## Inputs

- generated session script timeline;
- manual facilitator event markers;
- audio timestamps;
- music track timestamps;
- optional HR/HRV;
- optional EEG;
- participant verbal events;
- post-session notes.

## Outputs

- SessionTimeline
- SessionEvent list
- synchronized event report
- analysis-ready CSV/JSON export

## Event types

```text
script_phase_start
facilitator_spoke
music_changed
silence_started
participant_spoke
participant_cried
participant_reported_fear
participant_reported_insight
hrv_change_marker
eeg_pattern_change_marker
adverse_event
integration_note
```

## MVP mode

First implementation can be manual:

- timestamp button;
- event type dropdown;
- note field;
- export timeline.

Physiology can be added later.

## Cursor implementation notes

Suggested files:

```text
src/timeline/models.py
src/timeline/logger.py
src/timeline/exporter.py
app/pages/06_Timeline.py
tests/test_timeline_engine.py
```
