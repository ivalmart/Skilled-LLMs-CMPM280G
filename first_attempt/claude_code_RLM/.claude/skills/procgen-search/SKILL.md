---
name: procgen-search
description: Search the indexed procgen corpus using semantic similarity. Returns the most relevant document paths for a given query.
allowed-tools:
  - Bash
  - Read
---

# procgen-search (Vector Embedding Search)

Use this skill to find relevant procgen papers/documents for a given query.

## Why vector search?

The vector search approach is cleaner than a "librarian agent" because it's deterministic and fast. Rather than having an LLM guess which document is relevant, we compute semantic similarity directly using sentence-transformers embeddings.

## Prerequisites

Before first use, ensure the corpus is indexed:
```bash
python .claude/skills/procgen-search/scripts/index_corpus.py
```

Required packages: `sentence-transformers`, `numpy`

## Usage

This skill reads `$ARGUMENTS` as the search query.

Example: `/procgen-search WFC terrain generation with constraints`

## Procedure

1. Run the search script with the query:
   ```bash
   python .claude/skills/procgen-search/scripts/search_corpus.py "$ARGUMENTS" --json --top_k 3
   ```

2. Parse the JSON output to get the most relevant document path(s).

3. Return the results to the caller. The output includes:
   - `path`: Full path to the document
   - `filename`: Document filename
   - `similarity`: Cosine similarity score (0-1)
   - `preview`: First 500 chars of the document

## Integration with /rlm

After finding relevant documents, chain to the `/rlm` skill:
```
/rlm context=<best_path> query=<original_user_query>
```

## Reindexing

When new papers are added to `./corpus/`, reindex:
```bash
python .claude/skills/procgen-search/scripts/index_corpus.py
```
