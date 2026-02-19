import sys
import json
from pathlib import Path

SEARCH_SCRIPTS = Path(__file__).resolve().parents[2] / "procgen-search" / "scripts"
sys.path.insert(0, str(SEARCH_SCRIPTS))

MAX_CONTENT = 8000


def search(query, top_k=3):
    from search_corpus import search as corpus_search
    hits = corpus_search(query, top_k=top_k)

    results = []
    for hit in hits:
        p = Path(hit["path"])
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8", errors="ignore")[:MAX_CONTENT]
        results.append({
            "url": str(p),
            "title": hit["filename"],
            "content": content,
            "category": "LOCAL_CORPUS",
            "freshness": "TIMELESS",
        })
    return results


def main():
    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    print(json.dumps(search(query, top_k), indent=2))


if __name__ == "__main__":
    main()
