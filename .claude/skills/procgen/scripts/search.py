import sys
import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

API_KEY = os.environ["JINA_API_KEY"]
HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}
MAX_CONTENT = 8000


def fetch(endpoint, path):
    url = f"{endpoint}/{urllib.parse.quote(path, safe='')}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def search(query, count=5):
    data = fetch("https://s.jina.ai", query)
    items = data.get("data", [])[:count]
    results = []
    for item in items:
        url = item.get("url", "")
        title = item.get("title", "")
        snippet = item.get("description", "")
        content = ""
        try:
            page = fetch("https://r.jina.ai", url)
            content = (page.get("data", {}).get("content", "") or "")[:MAX_CONTENT]
        except Exception:
            pass
        results.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "content": content,
        })
    return results


def main():
    query = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    print(json.dumps(search(query, count), indent=2))


if __name__ == "__main__":
    main()
