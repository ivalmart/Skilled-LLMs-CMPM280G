import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

import _log

SCRIPTS = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
STATE_DIR = Path(__file__).resolve().parents[2] / "procgen_state"

UV = shutil.which("uv") if (ROOT / "pyproject.toml").exists() else None
PY = [UV, "run", "--project", str(ROOT), "python"] if UV else [sys.executable]


def run(script, args=None, stdin_data=None, fatal=True):
    cmd = PY + [str(SCRIPTS / script)] + (args or [])
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=sys.stderr, text=True,
    )
    stdout, _ = proc.communicate(input=stdin_data)
    if proc.returncode != 0:
        _log.fail(f"{script} exited with code {proc.returncode}")
        if fatal:
            sys.exit(1)
        return None
    return json.loads(stdout)


def execute(code, imports):
    for pkg in imports:
        if UV:
            subprocess.run([UV, "add", "--project", str(ROOT), pkg],
                          capture_output=True, text=True)
        else:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg],
                          capture_output=True, text=True)

    trial = SCRIPTS / "_trial.py"
    trial.write_text(code, encoding="utf-8")

    env = {**os.environ, "MPLBACKEND": "Agg"}
    try:
        result = subprocess.run(
            PY + [str(trial)], capture_output=True, text=True,
            timeout=30, env=env,
        )
    except subprocess.TimeoutExpired:
        trial.unlink(missing_ok=True)
        return (False, "TimeoutError", "execution exceeded 30s", "", "TimeoutExpired")

    trial.unlink(missing_ok=True)

    if result.returncode == 0:
        return (True, result.stdout.strip(), None, None, None)

    tb = result.stderr.strip()
    lines = tb.split("\n")
    error_line = ""
    error_type = "RuntimeError"
    error_msg = lines[-1] if lines else ""

    for line in lines:
        if line.strip().startswith("File") and "_trial.py" in line:
            error_line = line.strip()

    if ": " in error_msg:
        error_type, error_msg = error_msg.split(": ", 1)

    return (False, error_type, error_msg, error_line, tb)


def warden(original, refined, errors, prior_notes):
    payload = json.dumps({
        "original_code": original,
        "refined_code": refined,
        "errors": errors,
        "prior_notes": prior_notes,
    })
    result = run("warden.py", stdin_data=payload, fatal=False)
    if result is None:
        _log.fail("warden crashed, fail-closed")
        return {"approved": False, "notes": "warden unavailable"}
    return result


def main():
    _log.init()
    request = sys.argv[1]

    # 1. Decompose
    _log.stage("DECOMPOSE")
    problem = run("decompose.py", [request])
    ctypes = ", ".join(c["type"] for c in problem.get("constraints", []))
    _log.detail(f"output={problem['output_structure']}  constraints=[{ctypes}]")
    _log.elapsed()

    # 2. Memory lookup
    _log.stage("MEMORY LOOKUP")
    cached = run("memory.py", ["lookup"], json.dumps(problem))
    if cached and cached[0]["score"] >= 0.6:
        technique = cached[0]["technique"]
        _log.ok(f"cache hit: {technique['name']} (score={cached[0]['score']:.2f})")
        _log.elapsed()
        emit(request, problem, technique)
        return
    best_score = cached[0]["score"] if cached else 0
    _log.detail(f"cache miss (best score={best_score:.2f})")
    _log.elapsed()

    # 3. Build query — include original request keywords
    ctypes = " ".join(c["type"] for c in problem.get("constraints", []))
    query = f"procedural generation {request} {problem['output_structure']} {ctypes}"

    # 3a. Corpus search
    _log.stage("CORPUS SEARCH")
    _log.detail(f"query: {query}")
    corpus = run("corpus_search.py", [query])
    _log.ok(f"{len(corpus)} local hits")
    _log.elapsed()

    # 3b. Web search + verify
    _log.stage("WEB SEARCH")
    web = []
    try:
        results = run("search.py", [query])
        _log.detail(f"fetched {len(results)} results, verifying...")
        web = run("verify_source.py", stdin_data=json.dumps(results))
        _log.ok(f"{len(web)} sources passed verification")
    except SystemExit:
        _log.fail("web search failed, using corpus only")
    _log.elapsed()

    # 3c. Merge
    verified = corpus + web
    if not verified:
        _log.fail("no verified sources found")
        print(json.dumps({"error": "no verified sources found", "problem": problem}, indent=2))
        return

    # 5. Extract techniques
    _log.stage("EXTRACT")
    cards = []
    for i, src in enumerate(verified):
        _log.detail(f"[{i+1}/{len(verified)}] {src.get('title', src.get('url', '?'))}")
        payload = json.dumps({
            "content": src["content"],
            "url": src["url"],
            "problem": problem,
        })
        card = run("extract.py", stdin_data=payload)
        cards.append(card)
        _log.ok(f"  -> {card.get('name', '?')}")
        run("memory.py", ["save"], json.dumps(card))
    _log.elapsed()

    # 6. Select best technique (prefer web results over corpus on ties)
    _log.stage("SELECT")
    best = cards[0]
    best_overlap = 0
    ctarget = {c["type"] for c in problem.get("constraints", [])}
    for card in cards:
        overlap = len(set(card.get("constraint_types", [])) & ctarget)
        name = card.get("name", "?")
        _log.detail(f"  {name}: overlap={overlap}")
        if overlap >= best_overlap:
            best_overlap = overlap
            best = card
    _log.ok(f"selected: {best.get('name', '?')} (overlap={best_overlap})")
    _log.elapsed()

    emit(request, problem, best)


def emit(request, problem, technique):
    impl = technique.get("implementation", technique.get("implementation_pattern", {}))
    fp = technique.get("fingerprint", {})
    notes = technique.get("syntax_notes", [])

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

    MAX_RETRIES = 3
    MAX_LLM_FAILURES = 3
    errors = []
    code = None
    prev_code = None
    imports = []
    attempt = 0
    llm_failures = 0
    warden_rejections = 0
    warden_notes = ""
    last_degenerate = False

    while attempt < MAX_RETRIES and llm_failures < MAX_LLM_FAILURES:
        if attempt == 0 or code is None:
            _log.stage("SYNTHESIZE" if attempt == 0 else f"SYNTHESIZE (retry [{attempt+1}/{MAX_RETRIES}])")
            synth = run("synthesize.py", stdin_data=json.dumps({
                "request": request,
                "technique": technique,
                "syntax_notes": notes,
            }), fatal=False)
        else:
            _log.stage(f"REFINE [{attempt+1}/{MAX_RETRIES}]")
            payload = {
                "request": request,
                "technique": technique,
                "broken_code": code,
                "errors": errors,
                "syntax_notes": notes,
            }
            if warden_notes:
                payload["warden_notes"] = warden_notes
            synth = run("synthesize.py", stdin_data=json.dumps(payload), fatal=False)

        if synth is None:
            llm_failures += 1
            _log.fail(f"LLM failure {llm_failures}/{MAX_LLM_FAILURES}")
            _log.elapsed()
            errors.append({
                "attempt": attempt + 1,
                "error_type": "SynthesisFailure",
                "error_message": "synthesize.py crashed (likely LLM provider error)",
                "error_line": "",
                "traceback": "",
            })
            prev_code = code
            continue

        code = synth.get("code", "")
        imports = synth.get("imports", [])
        lines = len(code.strip().split("\n")) if code.strip() else 0
        _log.detail(f"generated {lines} lines, imports={imports}")
        _log.elapsed()

        if attempt > 0 and prev_code:
            _log.stage("WARDEN")
            verdict = warden(prev_code, code, errors, warden_notes)
            if not verdict.get("approved", False):
                warden_rejections += 1
                issues = verdict.get("api_issues", [])
                warden_notes = verdict.get("notes", "")
                if issues:
                    warden_notes += "\nAPI issues: " + "; ".join(issues)
                _log.fail(f"REJECTED: {warden_notes}")
                _log.elapsed()
                attempt += 1
                continue
            _log.ok("approved")
            _log.elapsed()

        _log.stage("EXECUTE")
        ok, stdout_or_etype, emsg, eline, tb = execute(code, imports)
        if ok:
            _log.ok(f"success on attempt {attempt + 1}")
            _log.elapsed()

            _log.stage("LAZY CHECK")
            lazy = run("lazy.py", stdin_data=json.dumps({
                "request": request,
                "technique_name": technique.get("name", ""),
                "stdout": stdout_or_etype or "",
                "code": code,
            }), fatal=False)
            if lazy and lazy.get("degenerate"):
                reason = lazy.get("reason", "degenerate output")
                _log.fail(reason)
                _log.elapsed()
                last_degenerate = True
                errors.append({
                    "attempt": attempt + 1,
                    "error_type": "DegenerateOutput",
                    "error_message": reason,
                    "error_line": "",
                    "traceback": "",
                })
                prev_code = code
                attempt += 1
                continue
            last_degenerate = False
            _log.ok("output looks genuine")
            _log.elapsed()
            break

        _log.fail(f"{stdout_or_etype}: {emsg}")
        if eline:
            _log.detail(eline)
        _log.elapsed()
        errors.append({
            "attempt": attempt + 1,
            "error_type": stdout_or_etype or "",
            "error_message": emsg or "",
            "error_line": eline or "",
            "traceback": tb or "",
        })
        prev_code = code
        attempt += 1

    if errors:
        _log.stage("MEMORY ANNOTATE")
        learned = [f"{e['error_type']}: {e['error_message']}" for e in errors]
        try:
            run("memory.py", ["annotate"], json.dumps({
                "technique_name": technique.get("name", ""),
                "syntax_notes": learned,
            }))
            _log.ok(f"saved {len(learned)} syntax notes")
        except SystemExit:
            _log.fail("annotation failed (non-fatal)")
        _log.elapsed()

    if last_degenerate:
        _log.fail("all attempts produced degenerate output")
        print(json.dumps({
            "error": "all attempts produced degenerate output",
            "problem": problem,
            "technique": technique.get("name", ""),
            "retry_count": attempt,
        }, indent=2))
        return

    output = {
        "problem": problem,
        "technique": technique.get("name", ""),
        "description": technique.get("description", ""),
        "code": code or "",
        "imports": imports,
        "fingerprint": fp,
        "anti_patterns": technique.get("anti_patterns", []),
        "sources": technique.get("sources", []),
        "retry_count": attempt,
        "warden_rejections": warden_rejections,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
