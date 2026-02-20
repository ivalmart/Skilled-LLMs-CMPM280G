import sys
import json
import _log
from llm import call
from _types import TechniqueCard, SynthesizedCode


def rebuild(d):
    impl = d.get("implementation", d.get("implementation_pattern", {}))
    if isinstance(impl, str):
        impl = {"pattern": impl}
    impl.setdefault("language", "python")
    impl.setdefault("dependencies", [])
    impl.setdefault("complexity", "moderate")
    d["implementation"] = impl

    fp = d.get("fingerprint", {})
    fp.setdefault("imports", [])
    fp.setdefault("file_artifacts", [])
    fp.setdefault("patterns", [])
    d["fingerprint"] = fp

    sources = []
    for s in d.get("sources", []):
        if isinstance(s, str):
            sources.append({"url": s, "category": "TUTORIAL", "accessed": ""})
        elif isinstance(s, dict):
            s.setdefault("category", "TUTORIAL")
            s.setdefault("accessed", "")
            sources.append(s)
    d["sources"] = sources

    d.setdefault("category", [])
    d.setdefault("problem_types", [])
    d.setdefault("constraint_types", [])
    d.setdefault("tradeoffs", [])
    d.setdefault("anti_patterns", [])
    d.setdefault("syntax_notes", [])
    d.setdefault("confidence", "")
    d.setdefault("description", "")
    return TechniqueCard.model_validate(d)


def main():
    data = json.loads(sys.stdin.read())
    technique = rebuild(data["technique"])
    notes = data.get("syntax_notes", technique.syntax_notes or [])

    try:
        if "errors" in data:
            nerr = len(data["errors"])
            _log.haiku(f"RefineCode ({nerr} error{'s' if nerr != 1 else ''})")
            prompt = _refine(data["request"], technique, data["broken_code"], data["errors"], notes)
        else:
            _log.haiku(f"SynthesizeCode ({technique.name})")
            prompt = _synth(data["request"], technique, notes)
        result = call(prompt, SynthesizedCode)
    except Exception as e:
        _log.fail(f"LLM call failed: {type(e).__name__}")
        sys.exit(1)

    d = result.model_dump()
    lines = len(d.get("code", "").strip().split("\n"))
    _log.detail(f"-> {lines} lines")
    print(json.dumps(d, indent=2))


def _synth(request, t, notes):
    ct = "\n".join(f"- {c.value}" for c in t.constraint_types) if t.constraint_types else "- (none specified)"
    notes_block = ""
    if notes:
        items = "\n".join(f"- {n}" for n in notes)
        notes_block = f"\nKnown syntax pitfalls for this technique (learned from prior runs):\n{items}\n"
    return f"""Write a complete, runnable Python file that implements the following procedural generation request
using the specified technique. Do NOT fall back to generate-and-test (random retry loops).

Request: {request}

Technique: {t.name}
Description: {t.description}
Implementation pattern:
{t.implementation.pattern}

Required imports/fingerprint: {t.fingerprint.imports}
Expected code patterns: {t.fingerprint.patterns}

Constraints to satisfy:
{ct}
{notes_block}
RULES:
- Output a single complete Python file that runs standalone
- Use the technique's implementation pattern, not random-retry
- Include a main() that demonstrates the generator with a printed example
- Keep it under 150 lines
- Ensure the file is syntactically complete and valid Python"""


def _refine(request, t, broken, errors, notes):
    err_lines = []
    for e in errors:
        err_lines.append(f"Attempt {e.get('attempt', '?')}: {e.get('error_type', '')} — {e.get('error_message', '')}")
        err_lines.append(f"Line: {e.get('error_line', '')}")
        err_lines.append(f"Traceback: {e.get('traceback', '')}")
    err_block = "\n".join(err_lines)
    notes_block = ""
    if notes:
        items = "\n".join(f"- {n}" for n in notes)
        notes_block = f"\nKnown syntax issues for this technique (from prior runs):\n{items}\n"
    return f"""Fix this broken procedural generation code. The previous attempt failed at runtime.

Request: {request}
Technique: {t.name}
Implementation pattern: {t.implementation.pattern}

Broken code:
{broken}

Errors encountered:
{err_block}
{notes_block}
RULES:
- Fix the actual errors, don't just rename variables or add comments
- Keep using the technique's implementation pattern
- Output a complete runnable Python file with valid syntax
- Keep it under 150 lines"""


if __name__ == "__main__":
    main()
