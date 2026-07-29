# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
This repo is an Obsidian vault (product spec / source of truth in the numbered `00_`–`23_` folders) plus a small Python package, `niros/`, that implements the active product: the **Human Understanding Engine (HUE) MVP**. The HUE is a self-contained Python library + CLI (a text-based adaptive psychological interview pipeline). There is **no web server, database, or background service** in the implemented code, so nothing needs to be "started" to develop or test it.

### Runtime & setup
- Python `>=3.11` is required (VM has 3.12). Dependencies are declared in `pyproject.toml`.
- Install (already handled by the startup update script): `pip install -e ".[dev]"`.
- `niros.egg-info/` is committed and gets rewritten by the editable install. Those churn changes are not meaningful — do not commit them (`git checkout -- niros.egg-info`).

### Test / build / run
- Tests: `python3 -m pytest` (config in `pyproject.toml`, `testpaths = ["tests"]`).
- Build: standard `pip install -e .` editable build; there is no separate build/bundle step.
- Run the MVP: `python3 demo_interview.py` — an interactive CLI that reads answers from stdin. Flags: `--turns N`, `--language {en,uk,ru,es}`, `--mode {passthrough,mock_llm}`, `--provider`.
  - Non-interactive run (useful for agents/CI): pipe answers, e.g. `printf "line1\nline2\n" | python3 demo_interview.py --turns 2`.

### Non-obvious gotchas
- **Pattern detection in the default `passthrough` mode is phrase-based**: it only fires when the input contains phrases from `knowledge/patterns/*.yaml` (`typical_phrases`). Arbitrary paraphrased text often yields "None detected", which is expected, not a bug. To exercise detection deterministically, use phrasing from the pattern YAML or the test fixtures (e.g. `"I worry people will stop liking me. I try to make everyone happy."`).
- For semantic (LLM-style) extraction use `--mode mock_llm`; the default provider is `mock` and needs **no network**. The real OpenAI provider (`--provider openai`) is fully optional and only needs `OPENAI_API_KEY` (loaded from a gitignored `.env` or env var).
- **No lint tooling is configured** (no ruff/flake8/black/mypy). "Lint" is not part of this project; only `pytest` is used.
