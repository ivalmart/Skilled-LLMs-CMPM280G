import sys
import json
from pathlib import Path
from datetime import datetime, timezone

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "procgen" / "scripts"
sys.path.insert(0, str(SCRIPTS))

ACTIVE = Path(__file__).resolve().parent.parent / "skills" / "procgen_state" / "active.json"
MAX_AGE_SECONDS = 600


def verify(code, state):
    from llm import call
    from _types import TechniqueVerification

    prompt = f"""Verify that this code actually uses the recommended procedural generation technique.

Technique: {state.get("technique", "")}

Expected fingerprint imports: {state.get("fingerprint_imports", [])}
Expected code patterns: {state.get("fingerprint_patterns", [])}
Anti-patterns (indicate generate-and-test fallback): {state.get("anti_patterns", [])}

Code to verify:
{code}

Check if the code contains the expected fingerprint signals and whether it contains any anti-patterns.
If it doesn't use the technique, identify what it defaulted to instead."""

    result = call(prompt, TechniqueVerification)

    if result.uses_technique:
        return True

    pattern = state.get("implementation_pattern", "")
    print(
        f"BLOCKED: Code does not use technique '{state.get('technique', '')}'.\n"
        f"Evidence: {result.evidence}\n"
        f"Anti-patterns found: {result.anti_patterns_found}\n"
        f"Defaulted to: {result.defaulted_to}\n"
        f"Expected implementation pattern:\n{pattern}",
        file=sys.stderr,
    )
    return False


def check(filepath):
    if not ACTIVE.exists():
        print("No active procgen state found.", file=sys.stderr)
        sys.exit(1)

    state = json.loads(ACTIVE.read_text(encoding="utf-8"))
    code = Path(filepath).read_text(encoding="utf-8")

    if not verify(code, state):
        sys.exit(1)
    print(f"OK: {filepath} uses technique '{state.get('technique', '')}'")


def hook():
    if not ACTIVE.exists():
        sys.exit(0)

    try:
        state = json.loads(ACTIVE.read_text(encoding="utf-8"))
    except Exception:
        sys.exit(0)

    ts = state.get("timestamp", "")
    if not ts:
        sys.exit(0)

    age = (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds()
    if age > MAX_AGE_SECONDS:
        sys.exit(0)

    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)

    name = payload.get("tool_name", "")
    inp = payload.get("tool_input", {})

    if name == "Write":
        path = inp.get("file_path", "")
        code = inp.get("content", "")
    elif name == "Edit":
        path = inp.get("file_path", "")
        code = inp.get("new_string", "")
    else:
        sys.exit(0)

    if not path.endswith(".py"):
        sys.exit(0)

    if not verify(code, state):
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--check":
        check(sys.argv[2])
    else:
        hook()
