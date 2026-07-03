# NIROS Real Interview Guide

This guide explains how to run NIROS with OpenAI for realistic intake interviews while keeping the mock provider for automated tests.

## API key setup

1. Create an OpenAI API key in your OpenAI account.
2. Either export it in your shell:

```bash
export OPENAI_API_KEY="your-key-here"
```

Or copy `.env.example` to `.env` at the repository root and set your key there:

```bash
cp .env.example .env
```

NIROS loads `.env` automatically at startup. Existing shell environment variables are not overwritten.

3. Do not commit the key to git or paste it into NIROS output.

When `OPENAI_API_KEY` is present, NIROS defaults to the OpenAI semantic provider at runtime.

When the key is missing, NIROS falls back to the mock provider and prints a clear message explaining why.

## Launching NIROS

From the repository root:

```bash
python scripts/run_niros.py
```

Or use the interview demo directly:

```bash
python demo_interview.py
```

Both entry points support the same runtime provider selection rules.

## Switching providers

### Automatic selection (recommended)

- `OPENAI_API_KEY` set → default provider is `openai` (REAL runtime)
- `OPENAI_API_KEY` missing → default provider is `mock` (TEST runtime)

### Explicit runtime modes

```bash
python scripts/run_niros.py --runtime test
python scripts/run_niros.py --runtime real
```

- `test` → mock provider
- `real` → openai provider when the API key exists, otherwise mock with a fallback message

### Explicit provider override

```bash
python scripts/run_niros.py --provider mock
python scripts/run_niros.py --provider openai
```

## Enabling debug mode

Debug mode prints the full understanding pipeline for each interview turn:

1. Raw transcript
2. Semantic Facts
3. Detected Patterns
4. Human Digital Fingerprint

Example:

```bash
python scripts/run_niros.py --provider openai --debug --turns 3
```

Or with automatic provider selection when the key is configured:

```bash
python scripts/run_niros.py --debug --runtime real --turns 3
```

Debug mode does not print API keys or provider secrets.

## Architecture notes

- OpenAI extracts **Semantic Facts only**.
- NIROS Core owns pattern detection, hypotheses, profile building, and scenario planning.
- Automated tests continue to use the mock provider by default.
- Phrase-based pattern detection still runs on interview transcript text; semantic facts are an additional observed layer.

## Troubleshooting

- If REAL mode falls back to mock, verify `OPENAI_API_KEY` is exported in the same shell session.
- If OpenAI returns no facts, check network access and confirm the `openai` package is installed.
- For deterministic CI and unit tests, keep using `--runtime test` or `--provider mock`.
