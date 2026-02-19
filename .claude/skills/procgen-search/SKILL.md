---
name: procgen-search
description: "[Internal] Low-level corpus search utility. Called automatically by /procgen — not intended for direct use."
allowed-tools:
  - Bash
  - Read
---

# procgen-search (Internal Utility)

Low-level vector similarity search against the indexed procgen corpus. Called automatically by `/procgen` via `corpus_search.py` — use `/procgen` instead.

## Prerequisites

Before first use, ensure the corpus is indexed:
```bash
python .claude/skills/procgen-search/scripts/index_corpus.py
```

Required packages: `sentence-transformers`, `numpy`

## Direct usage (debugging only)

```bash
python .claude/skills/procgen-search/scripts/search_corpus.py "$ARGUMENTS" --json --top_k 3
```

Output fields: `path`, `filename`, `similarity`, `preview`

## Reindexing

When new papers are added to `./corpus/`, reindex:
```bash
python .claude/skills/procgen-search/scripts/index_corpus.py
```
