import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

import _log
from baml_client.sync_client import b


def main():
    results = json.loads(sys.stdin.read())
    verified = []
    for i, r in enumerate(results):
        _log.haiku(f"VerifySource [{i+1}/{len(results)}]")
        _log.detail(f"  {r['title'][:60]}")
        try:
            source = b.VerifySource(url=r["url"], title=r["title"], snippet=r["snippet"])
        except Exception as e:
            _log.fail(f"  BAML call failed: {type(e).__name__}")
            continue
        if not source.should_use:
            _log.fail(f"  rejected ({source.category.value})")
            continue
        _log.ok(f"  accepted ({source.category.value}, {source.freshness.value})")
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
