---
description: "Procedural generation knowledge system — finds and applies PCG techniques"
---

# Procgen

Run the procgen knowledge pipeline. A small model (Haiku) does all code synthesis — you are just the orchestrator.

## Step 1: Run the pipeline

Run this command in the terminal:

```bash
cd {{cwd}} && uv run python .claude/skills/procgen/scripts/pipeline.py "{{input}}"
```

The pipeline takes 30-120 seconds.

## Step 2: Handle the output

The pipeline prints JSON to stdout containing:
- `code` — complete runnable Python file
- `imports` — pip dependencies
- `technique` — technique name used
- `sources` — references

Write the `code` field to a `.py` file. Do NOT rewrite or modify the generated code — Haiku is the synthesizer, not you. Only make minimal edits (fix imports, rename output file) if the user asks.

If the pipeline exits non-zero or finds no technique, say so. Do not write your own generator.

## Step 3: Verify the output

After writing the file, run verification:

```bash
uv run python .claude/hooks/verify_procgen.py --check <path-to-written-file>
```

If verification fails, the code fell back to generate-and-test. Re-run the pipeline or ask the user.

## Important
- Anti-patterns like `while attempts < N` with `random.randint` indicate generate-and-test fallback
- The pipeline manages its own technique memory in `.claude/knowledge/techniques.md`
- Sources are verified for quality before techniques are extracted
