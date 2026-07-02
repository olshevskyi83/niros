# Sprint 002 — Big Five Module Implementation Design

## Goal

Design the first working NIROS psychological assessment module: Big Five.

The goal is not to create a publication-grade personality test, but to define a practical MVP module that can produce structured psychological signals for the NIROS Reasoning Engine.

## Module

Big Five

## Research status

Research completed in Sprint 001.

Foundation note:

- [[Big_Five_Foundation]]

## Scope

- Questionnaire structure
- Trait and facet model
- Scoring algorithm
- Confidence estimation
- Internal data model
- Module API
- Reasoning Engine integration
- Code architecture

## Not in scope

- New literature search
- Clinical diagnosis
- Psychedelic dosing recommendations
- Final UI implementation
- Production code

## Definition of done

Sprint 002 is complete when NIROS has a clear implementation specification for the Big Five module, including:

- question format
- scoring rules
- result JSON
- API contract
- reasoning integration rules
- code module structure

## Core principle

Big Five does not decide therapy.

Big Five provides personality signals that other NIROS modules combine with attachment, emotion regulation, trauma, absorption, suggestibility, values, mental health screening, and psychedelic history.