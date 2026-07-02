# Module Registry

## Status

Architecture Design

Sprint 003

---

# Purpose

The Module Registry is responsible for managing all psychological assessment modules available within NIROS.

It acts as a central catalogue that allows the Core Engine to discover, initialize and communicate with assessment modules through a common interface.

The registry does not contain assessment logic.

---

# Responsibilities

The Module Registry is responsible for:

- registering available modules
- exposing module metadata
- tracking module versions
- initializing modules
- validating module compatibility
- providing a unified interface to the Core Engine

---

# Registered Modules

The initial NIROS modules are:

| Module | Status |
|---------|--------|
| Big Five | Planned |
| Attachment | Planned |
| Emotion Regulation | Planned |
| Absorption | Planned |
| Suggestibility | Planned |
| Trauma | Planned |
| Values | Planned |
| Cognitive Style | Planned |
| Motivation | Planned |
| Psychedelic History | Planned |
| Mental Health Screening | Planned |
| Conversation Assessment | Planned |

New modules can be added without modifying the Core Engine.

---

# Standard Module Interface

Every module must expose the same interface.

```python
start_assessment()

submit_response()

validate()

score()

generate_signals()

get_result()
```

The Core Engine communicates only through this interface.

---

# Module Metadata

Each module provides:

- module name
- version
- assessment type
- supported languages
- supported signals
- dependencies

Example:

```json
{
  "module": "big_five",
  "version": "1.0",
  "assessment": "BFI-2",
  "signals": [
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism"
  ]
}
```

---

# Design Principles

The Module Registry should be:

- lightweight
- modular
- extensible
- independent of implementation details

It should never perform scoring or reasoning.

---

# Summary

The Module Registry is the entry point for all NIROS psychological assessment modules.

Its role is to make modules discoverable and provide a consistent interface for the Core Engine.