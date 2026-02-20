import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

import _log
from baml_client.sync_client import b
from baml_client.types import ProcgenProblem, Constraint, OutputType, ConstraintType


def rebuild(d):
    return ProcgenProblem(
        output_structure=OutputType(d["output_structure"]),
        constraints=[
            Constraint(
                name=c["name"],
                type=ConstraintType(c["type"]),
                description=c["description"],
            )
            for c in d["constraints"]
        ],
        scale=d["scale"],
        realtime=d["realtime"],
    )


def main():
    data = json.loads(sys.stdin.read())
    problem = rebuild(data["problem"])
    _log.haiku("ExtractTechnique")
    try:
        result = b.ExtractTechnique(
            content=data["content"],
            url=data["url"],
            problem=problem,
        )
    except Exception as e:
        _log.fail(f"BAML call failed: {type(e).__name__}")
        sys.exit(1)
    d = result.model_dump()
    _log.detail(f"-> {d.get('name', '?')}")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
