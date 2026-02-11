"""
Searches the indexed corpus using semantic similarity.

The vector search approach is cleaner than a "librarian agent" because it's
deterministic and fast.

Automatically indexes new papers found in corpus/ before searching.

Usage:
    python search_corpus.py "your query here" [--top_k 3]
"""

import argparse
import pickle
import sys
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Run: pip install sentence-transformers numpy")
    exit(1)

CORPUS_DIR = Path(__file__).resolve().parents[4] / "corpus"
INDEX_PATH = Path(__file__).resolve().parents[4] / ".claude" / "rlm_state" / "corpus_index.pkl"

def check_and_index_new_papers():
    new_files = list(CORPUS_DIR.glob("*.txt"))
    if not new_files:
        return False

    print(f"Found {len(new_files)} new paper(s) to index...")
    from index_corpus import create_index
    create_index()
    return True

def dot_score(a, b):
    return np.dot(a, b)

def search(query: str, top_k: int = 3):
    check_and_index_new_papers()

    if not INDEX_PATH.exists():
        print(f"ERROR: No index found and no papers in corpus/")
        print(f"Add .txt files to: {CORPUS_DIR}")
        return []

    with open(INDEX_PATH, "rb") as f:
        index = pickle.load(f)

    model = SentenceTransformer(index["model"])
    query_embedding = model.encode(query)

    similarities = []
    for i, doc_embedding in enumerate(index["embeddings"]):
        sim = dot_score(query_embedding, doc_embedding)
        similarities.append((sim, i))

    similarities.sort(reverse=True)

    results = []
    for sim, idx in similarities[:top_k]:
        doc = index["documents"][idx]
        results.append({
            "path": doc["path"],
            "filename": doc["filename"],
            "similarity": float(sim),
            "preview": doc["preview"]
        })

    return results

def main():
    parser = argparse.ArgumentParser(description="Search the procgen corpus")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top_k", type=int, default=3, help="Number of results to return")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = search(args.query, args.top_k)

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        if not results:
            print("No results found.")
            return

        print(f"\nTop {len(results)} results for: '{args.query}'\n")
        print("-" * 60)
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['filename']}")
            print(f"   Similarity: {r['similarity']:.4f}")
            print(f"   Path: {r['path']}")
            print(f"   Preview: {r['preview'][:100]}...")
            print()

if __name__ == "__main__":
    main()
