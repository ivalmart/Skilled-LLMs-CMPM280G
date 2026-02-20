import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

import _log
from baml_client.sync_client import b


def main():
    data = json.loads(sys.stdin.read())
    _log.haiku("CheckLazy")
    try:
        verdict = b.CheckLazy(
            request=data["request"],
            technique_name=data["technique_name"],
            stdout=data["stdout"],
        )
    except Exception as e:
        _log.fail(f"BAML call failed: {type(e).__name__}")
        sys.exit(1)
    d = verdict.model_dump()
    if d.get("degenerate"):
        _log.fail(f"degenerate: {d.get('reason', '')}")
    else:
        _log.ok("output looks genuine")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
