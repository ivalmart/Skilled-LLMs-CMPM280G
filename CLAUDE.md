# Project instructions

We are investigating giving mid-sized LLMs useful access to the deep knowledge of academic and practitioner procgen methods so that they are more effective in engineering software that does not utilize AI agents. Rather than attempting to create programs off of their pretraining data, they have the ability to recall their deep knowledge that they actively learned. The primary methodology for obtaining this knowledge will be through an RLM.

## Architecture

This repository includes:
- **Skill**: `rlm` in `.claude/skills/rlm/` - orchestrates chunk-level processing of large documents
- **Skill**: `procgen-search` in `.claude/skills/procgen-search/` - vector embedding search over the corpus
- **Subagent**: `rlm-subcall` in `.claude/agents/` - extracts relevant info from individual chunks
- **Subagent**: `procgen-classifier` in `.claude/agents/` - classifies if a query relates to procgen
- **Corpus**: `./corpus/` - academic papers converted to text (index with `index_corpus.py`)

## Implicit Procgen Recognition (ALWAYS DO THIS)

**On every user query**, you must:

1. **Classify the query** using the `procgen-classifier` subagent:
   ```
   Task tool → subagent_type: procgen-classifier
   prompt: "Classify this query: <user's question>"
   ```

2. **If `is_procgen: true`** with medium or high confidence:
   - Run `/procgen-search <user's query>` to find relevant documents
   - Take the top result's path
   - Run `/rlm context=<path> query=<user's query>`
   - Synthesize the answer using the extracted knowledge

3. **If `is_procgen: false`** or low confidence:
   - Answer normally without the RLM pipeline

## Manual Usage

Users can also explicitly invoke:
- `/procgen-search <query>` - just find relevant documents
- `/rlm context=<path> query=<question>` - process a specific document

## Setup

Before first use:
```bash
pip install sentence-transformers numpy
python .claude/skills/procgen-search/scripts/index_corpus.py
```

Add papers to `./corpus/` as `.txt` or `.md` files, then reindex.

## Design Rationale

The vector search approach is cleaner than a "librarian agent" because it's deterministic and fast. Rather than having an LLM guess which document is relevant, we compute semantic similarity directly.

Keep the main conversation light: use the REPL and subagent to do chunk-level work, then synthesize.
