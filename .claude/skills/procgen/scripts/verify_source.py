import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from baml_client.sync_client import b


def main():
    results = json.loads(sys.stdin.read())
    verified = []
    for r in results:
        source = b.VerifySource(url=r["url"], title=r["title"], snippet=r["snippet"])
        if not source.should_use:
            continue
        verified.append({
            "url": r["url"],
            "title": r["title"],
            "content": r.get("content", ""),
            "category": source.category.value,
            "freshness": source.freshness.value,
        })
    print(json.dumps(verified, indent=2))


if __name__ == "__main__":
    main()
