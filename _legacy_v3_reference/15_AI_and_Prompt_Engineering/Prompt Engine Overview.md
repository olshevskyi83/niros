---
title: Prompt Engine Overview
project: NeuroIcaro Research Platform
status: draft
tags: [neuroicaro]
---

# Prompt Engine Overview

## Purpose

The Prompt Engine controls how LLMs transform profile data into structured outputs.

## Must enforce

- evidence labels;
- safety constraints;
- no diagnosis without clinician;
- no unsupported cure claims;
- no manipulation;
- transparent uncertainty.

## Prompt layers

1. System safety prompt.
2. Clinical boundaries prompt.
3. Profile interpretation prompt.
4. Therapeutic target prompt.
5. Script generation prompt.
6. Quality control prompt.
