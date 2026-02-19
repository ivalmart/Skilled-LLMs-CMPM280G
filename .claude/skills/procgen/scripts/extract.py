import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

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
    result = b.ExtractTechnique(
        content=data["content"],
        url=data["url"],
        problem=problem,
    )
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
