import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

import _log
from baml_client.sync_client import b
from baml_client.types import RefinementError


def main():
    data = json.loads(sys.stdin.read())
    _log.haiku("WatchRefinement")
    try:
        errors = [RefinementError(**e) for e in data["errors"]]
        verdict = b.WatchRefinement(
            original_code=data["original_code"],
            refined_code=data["refined_code"],
            errors=errors,
            warden_notes=data.get("prior_notes", ""),
        )
    except Exception as e:
        _log.fail(f"BAML call failed: {type(e).__name__}")
        sys.exit(1)
    d = verdict.model_dump()
    if d.get("approved"):
        _log.ok("approved")
    else:
        _log.fail(f"rejected: {d.get('notes', '')}")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
