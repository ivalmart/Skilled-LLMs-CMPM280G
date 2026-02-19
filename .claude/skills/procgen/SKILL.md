---
description: Procedural generation knowledge system — finds and applies PCG techniques
allowed_tools: Bash, Read, Write, Glob, Grep
---

# /procgen

Run the procgen knowledge pipeline to find the right technique for a procedural generation task.

## Usage
/procgen <description of what to generate>

## Procedure

1. Run the pipeline:
```bash
python .claude/skills/procgen/scripts/pipeline.py "$ARGUMENTS"
```

2. The pipeline outputs JSON containing:
   - `code`: a complete runnable Python file synthesized by Haiku
   - `imports`: any pip dependencies needed
   - `technique`: the technique name used
   - `sources`: references

3. Write the `code` field to a `.py` file. Do NOT rewrite or substantially modify the generated code — Haiku is the code synthesizer, not you. You may only make minimal edits (fix imports, rename the output file) if the user requests them.

4. If the pipeline finds no matching technique, say so explicitly. Do not write your own generator.

## Important
- The PostToolUse hook will verify your code uses the recommended technique
- If verification fails, you'll be re-prompted with the recipe code
- Anti-patterns like `while attempts < N` with `random.randint` will be caught
