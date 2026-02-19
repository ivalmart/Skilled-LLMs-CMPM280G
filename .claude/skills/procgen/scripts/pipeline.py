import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

SCRIPTS = Path(__file__).resolve().parent
STATE_DIR = Path(__file__).resolve().parents[2] / "procgen_state"
PY = sys.executable


def run(script, args=None, stdin_data=None):
    cmd = [PY, str(SCRIPTS / script)] + (args or [])
    env = {**__import__('os').environ, "BAML_LOG": "off"}
    result = subprocess.run(
        cmd, input=stdin_data, capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        print(f"Error in {script}: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def main():
    request = sys.argv[1]

    # 1. Decompose
    problem = run("decompose.py", [request])
    print(f"[decompose] output_structure={problem['output_structure']}", file=sys.stderr)

    # 2. Memory lookup
    cached = run("memory.py", ["lookup"], json.dumps(problem))
    if cached and cached[0]["score"] >= 0.5:
        technique = cached[0]["technique"]
        print(f"[memory] cache hit: {technique['name']}", file=sys.stderr)
        emit(request, problem, technique)
        return

    # 3. Build query
    ctypes = " ".join(c["type"] for c in problem.get("constraints", []))
    query = f"procedural generation {problem['output_structure']} {ctypes}"
    print(f"[search] query: {query}", file=sys.stderr)

    # 3a. Corpus search (pre-vetted, skip verification)
    corpus = run("corpus_search.py", [query])
    print(f"[corpus] {len(corpus)} local hits", file=sys.stderr)

    # 3b. Web search + verify (best-effort)
    web = []
    try:
        results = run("search.py", [query])
        web = run("verify_source.py", stdin_data=json.dumps(results))
        print(f"[verify] {len(web)} web sources passed", file=sys.stderr)
    except SystemExit:
        print("[verify] web search failed, using corpus only", file=sys.stderr)

    # 3c. Merge (corpus first — higher trust)
    verified = corpus + web
    if not verified:
        print(json.dumps({"error": "no verified sources found", "problem": problem}, indent=2))
        return

    # 5. Extract techniques
    cards = []
    for src in verified:
        payload = json.dumps({
            "content": src["content"],
            "url": src["url"],
            "problem": problem,
        })
        card = run("extract.py", stdin_data=payload)
        cards.append(card)
        run("memory.py", ["save"], json.dumps(card))

    # 6. Select best technique
    best = cards[0]
    best_overlap = 0
    ctarget = {c["type"] for c in problem.get("constraints", [])}
    for card in cards:
        overlap = len(set(card.get("constraint_types", [])) & ctarget)
        if overlap > best_overlap:
            best_overlap = overlap
            best = card

    emit(request, problem, best)


def emit(request, problem, technique):
    impl = technique.get("implementation", technique.get("implementation_pattern", {}))
    fp = technique.get("fingerprint", {})

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    active = {
        "technique": technique.get("name", ""),
        "fingerprint_imports": fp.get("imports", []),
        "fingerprint_patterns": fp.get("patterns", []),
        "anti_patterns": technique.get("anti_patterns", []),
        "implementation_pattern": impl.get("pattern", "") if isinstance(impl, dict) else str(impl),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (STATE_DIR / "active.json").write_text(json.dumps(active, indent=2), encoding="utf-8")

    # synthesize code via Haiku
    print("[synthesize] generating code via Haiku...", file=sys.stderr)
    synth = run("synthesize.py", stdin_data=json.dumps({
        "request": request,
        "technique": technique,
    }))

    output = {
        "problem": problem,
        "technique": technique.get("name", ""),
        "description": technique.get("description", ""),
        "code": synth.get("code", ""),
        "imports": synth.get("imports", []),
        "fingerprint": fp,
        "anti_patterns": technique.get("anti_patterns", []),
        "sources": technique.get("sources", []),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
