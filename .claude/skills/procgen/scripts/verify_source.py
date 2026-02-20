import sys
import json
import _log
from llm import call
from _types import Source


def main():
    results = json.loads(sys.stdin.read())
    verified = []
    for i, r in enumerate(results):
        _log.haiku(f"VerifySource [{i+1}/{len(results)}]")
        _log.detail(f"  {r['title'][:60]}")
        prompt = f"""Evaluate this web source for reliability as a procedural generation reference.

URL: {r["url"]}
Title: {r["title"]}
Snippet: {r["snippet"]}

Classify the source category, freshness, and whether it should be used.
Set should_use to false for AI-generated content, unknown blogs without citations, or stale implementations.

Source categories: ACADEMIC (arxiv, ACM, IEEE), OFFICIAL_DOCS, TUTORIAL, BLOG_REPUTABLE, BLOG_UNKNOWN, FORUM, GENERATED.
Freshness: CURRENT (within 2 years or stable algorithm), DATED (2-5 years), STALE (5+ years), TIMELESS (mathematical)."""
        try:
            source = call(prompt, Source)
        except Exception as e:
            _log.fail(f"  LLM call failed: {type(e).__name__}")
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
