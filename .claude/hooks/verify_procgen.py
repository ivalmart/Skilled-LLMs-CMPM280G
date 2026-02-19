import sys
import json
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ACTIVE = Path(__file__).resolve().parent.parent / "procgen_state" / "active.json"
MAX_AGE_SECONDS = 600


def main():
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
        hook = json.loads(raw)
    except Exception:
        sys.exit(0)

    name = hook.get("tool_name", "")
    inp = hook.get("tool_input", {})

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

    from baml_client.sync_client import b

    result = b.VerifyTechnique(
        code=code,
        technique_name=state.get("technique", ""),
        fingerprint_imports=state.get("fingerprint_imports", []),
        fingerprint_patterns=state.get("fingerprint_patterns", []),
        anti_patterns=state.get("anti_patterns", []),
    )

    if result.uses_technique:
        sys.exit(0)

    pattern = state.get("implementation_pattern", "")
    print(
        f"BLOCKED: Code does not use technique '{state.get('technique', '')}'.\n"
        f"Evidence: {result.evidence}\n"
        f"Anti-patterns found: {result.anti_patterns_found}\n"
        f"Defaulted to: {result.defaulted_to}\n"
        f"Expected implementation pattern:\n{pattern}",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
