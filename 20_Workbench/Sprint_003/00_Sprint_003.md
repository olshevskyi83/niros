# Sprint 003 — NIROS Core Architecture

## Status

Architecture Design

---

# Goal

Design the core architecture of NIROS before writing production code.

The goal is to define how all psychological modules will interact with the central NIROS engine.

This sprint transforms NIROS from a collection of assessment modules into a unified Psychological Engine.

---

# Why This Sprint Exists

Sprint 002 designed the first assessment module: Big Five.

However, NIROS is not a Big Five app.

NIROS is a modular psychological assessment and reasoning platform.

Before implementing code, the system needs a shared architecture for:

- Psychological Signals
- Module Registry
- Psychological Profile Engine
- Reasoning Engine
- Conversation Assessment
- Recommendation Layer
- Longitudinal Profile Updates

---

# Scope

Sprint 003 defines:

- NIROS Core system architecture
- Universal Psychological Signal Model
- Module Registry
- Psychological Profile Engine
- Reasoning Engine
- Conversation Assessment Engine
- Recommendation Interface
- End-to-end assessment pipeline

---

# Not in Scope

This sprint does not include:

- new psychological research
- new questionnaire design
- clinical protocols
- psychedelic dosing
- UI design
- production code

---

# Core Principle

NIROS should not be built as a set of independent questionnaires.

NIROS should be built as a modular Psychological Engine.

Each module produces standardized Psychological Signals.

The Core Engine integrates these signals into a unified psychological representation.

---

# Sprint Deliverables

This sprint should produce the following files:

- 01_NIROS_Core_System_Architecture.md
- 02_Universal_Psychological_Signal_Model.md
- 03_Module_Registry.md
- 04_Psychological_Profile_Engine.md
- 05_Reasoning_Engine.md
- 06_Conversation_Assessment_Engine.md
- 07_Recommendation_Interface.md
- 08_End_to_End_Assessment_Pipeline.md

---

# Definition of Done

Sprint 003 is complete when NIROS has a clear architecture for how psychological modules, AI conversation, reasoning and recommendations work together.

After this sprint, Big Five can be implemented as the first production module inside the NIROS Core architecture.