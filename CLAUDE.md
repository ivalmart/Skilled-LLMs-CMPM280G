# Procgen Knowledge System

This project implements a knowledge pipeline that helps LLMs write procedural generators using proper PCG techniques instead of defaulting to generate-and-test.

## System overview
See `design_fiction.md` for the full vision.

## Key components
- `.claude/skills/procgen/scripts/llm.py` — OpenAI SDK client (OpenRouter), JSON parsing, `call(prompt, cls)`
- `.claude/skills/procgen/scripts/_types.py` — Pydantic models (replaces BAML types)
- `.claude/skills/procgen/scripts/pipeline.py` — main pipeline orchestrator (retry loop + warden gate)
- `.claude/skills/procgen/scripts/synthesize.py` — code synthesis + refinement
- `.claude/skills/procgen/scripts/memory.py` — technique memory with embedding similarity scoring
- `.claude/skills/procgen/scripts/warden.py` — Warden agent (gates refinements)
- `.claude/hooks/verify_procgen.py` — PostToolUse hook verifying code uses recommended technique
- `.claude/knowledge/techniques.md` — growing technique memory (self-populating)
- `.claude/skills/procgen_state/active.json` — transient state for hook communication

## Environment variables
- `OPENROUTER_API_KEY` — for LLM calls via OpenRouter
- `SMALL_MODEL` — model identifier (default: `anthropic/claude-3.5-haiku`)
- `JINA_API_KEY` — optional, for Jina web search (falls back to DuckDuckGo if absent)

## Usage
```
/procgen <description of what to generate>
```

## Runtime verification loop
The retry loop uses separate budgets: `attempt` (max 3) for code execution failures, `llm_failures` (max 3) for LLM parse failures (synthesize returns None). LLM failures don't burn code-fix retries. The Warden is fail-closed: if it crashes, the refinement is rejected. Warden checks cosmetic-only changes, repeated errors, and API correctness (wrong kwargs, bad signatures, workaround patterns). `WardenVerdict` includes `api_issues: list[str]`.

## Coding rules
- No docstrings on files or functions
- Prefer single-word variable/function names
- No `else` — use early returns
- Avoid mocks in tests
