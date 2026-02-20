import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

import _log
from baml_client.sync_client import b


def main():
    _log.haiku("DecomposeProblem")
    try:
        result = b.DecomposeProblem(sys.argv[1])
    except Exception as e:
        _log.fail(f"BAML call failed: {type(e).__name__}")
        sys.exit(1)
    d = result.model_dump()
    _log.detail(f"-> {d['output_structure']}, {len(d['constraints'])} constraints")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
