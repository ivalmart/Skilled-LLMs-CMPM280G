# Procgen Knowledge System

This project implements a knowledge pipeline that helps LLMs write procedural generators using proper PCG techniques instead of defaulting to generate-and-test.

## System overview
See `design_fiction.md` for the full vision.

## Key components
- `baml_src/` — BAML schema definitions (types, functions, clients)
- `baml_client/` — auto-generated Python client (do not edit)
- `.claude/skills/procgen/` — `/procgen` slash command and pipeline scripts
- `.claude/hooks/verify_procgen.py` — PostToolUse hook verifying code uses recommended technique
- `.claude/knowledge/techniques.md` — growing technique memory (starts empty, self-populating)
- `.claude/procgen_state/active.json` — transient state for hook communication

## Environment variables
- `OPENROUTER_API_KEY` — for BAML Haiku calls via OpenRouter
- `JINA_API_KEY` — for web search and reader (never hardcode)

## Usage
```
/procgen <description of what to generate>
```

## Coding rules
- No docstrings on files or functions
- Prefer single-word variable/function names
- No `else` — use early returns
- Avoid mocks in tests
