import sys
import json
import os
import re
import urllib.request
import urllib.parse

import _log

JINA_KEY = os.environ.get("JINA_API_KEY")
MAX_CONTENT = 8000


def strip(html):
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:MAX_CONTENT]


def fetch(endpoint, path):
    url = f"{endpoint}/{urllib.parse.quote(path, safe='')}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {JINA_KEY}",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def jina(query, count=5):
    _log.detail(f"jina search: {query}")
    data = fetch("https://s.jina.ai", query)
    items = data.get("data", [])[:count]
    results = []
    for i, item in enumerate(items):
        url = item.get("url", "")
        title = item.get("title", "")
        snippet = item.get("description", "")
        _log.detail(f"  [{i+1}] reading: {title[:50]}")
        content = ""
        try:
            page = fetch("https://r.jina.ai", url)
            content = (page.get("data", {}).get("content", "") or "")[:MAX_CONTENT]
        except Exception:
            _log.fail(f"  [{i+1}] failed to fetch content")
        results.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "content": content,
        })
    return results


def ddg(query, count=5):
    _log.detail(f"duckduckgo search: {query}")
    from ddgs import DDGS
    with DDGS() as d:
        hits = list(d.text(query, max_results=count))
    results = []
    for i, hit in enumerate(hits):
        url = hit.get("href", "")
        title = hit.get("title", "")
        body = hit.get("body", "")
        _log.detail(f"  [{i+1}] {title[:50]}")
        content = body
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; procgen-search/1.0)"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                content = strip(raw) or body
        except Exception:
            _log.fail(f"  [{i+1}] failed to fetch content, using snippet")
        results.append({
            "url": url,
            "title": title,
            "snippet": body,
            "content": content,
        })
    return results


def search(query, count=5):
    if JINA_KEY:
        try:
            return jina(query, count)
        except Exception as e:
            _log.fail(f"jina failed ({e}), falling back to duckduckgo")
    return ddg(query, count)


def main():
    query = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    print(json.dumps(search(query, count), indent=2))


if __name__ == "__main__":
    main()
