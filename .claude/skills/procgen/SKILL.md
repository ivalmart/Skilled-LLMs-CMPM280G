---
description: Procedural generation knowledge system — finds and applies PCG techniques
allowed_tools: Bash, Read, Write, Glob, Grep
---

# /procgen

Run the procgen knowledge pipeline. A small model (GLM-5) does all code synthesis — you are just the orchestrator.

## Step 1: Run the pipeline

Use the **Bash** tool with this exact command:

```bash
cd /c/Users/jperr/Documents/CMPM280G/rlm && uv run python .claude/skills/procgen/scripts/pipeline.py "$ARGUMENTS"
```

The pipeline takes 30-120 seconds. Run it with a 300s timeout.

## Step 2: Monitor progress (optional)

While the pipeline runs, you can read the progress log:

```bash
cat .claude/skills/procgen/scripts/_progress.log
```

Each line shows `{timestamp} {EVENT} {details}`. If the last line is an `LLM` event older than 60s, the GLM-5 call may be hanging.

## Step 3: Handle the output

The pipeline prints JSON to stdout containing:
- `code` — complete runnable Python file
- `imports` — pip dependencies
- `technique` — technique name used
- `sources` — references

Write the `code` field to a `.py` file. Do NOT rewrite or modify the generated code — GLM-5 is the synthesizer, not you. Only make minimal edits (fix imports, rename output file) if the user asks.

If the pipeline exits non-zero or finds no technique, say so. Do not write your own generator.

## Important
- The PostToolUse hook verifies the code uses the recommended technique
- If verification fails, you'll be re-prompted with the recipe code
- Anti-patterns like `while attempts < N` with `random.randint` will be caught
