import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from baml_client.sync_client import b
from baml_client.types import (
    TechniqueCard, Implementation, Fingerprint, SourceRef, Tradeoff,
    OutputType, ConstraintType, SourceCategory,
)


def rebuild(d):
    return TechniqueCard(
        name=d["name"],
        category=d.get("category", []),
        problem_types=[OutputType(p) for p in d.get("problem_types", [])],
        constraint_types=[ConstraintType(c) for c in d.get("constraint_types", [])],
        description=d.get("description", ""),
        tradeoffs=[Tradeoff(**t) for t in d.get("tradeoffs", [])],
        implementation=Implementation(**d.get("implementation", d.get("implementation_pattern", {}))),
        sources=[SourceRef(url=s.get("url", ""), category=SourceCategory(s["category"]), accessed=s.get("accessed", "")) for s in d.get("sources", [])],
        fingerprint=Fingerprint(**d.get("fingerprint", {})),
        anti_patterns=d.get("anti_patterns", []),
        confidence=d.get("confidence", ""),
    )


def main():
    data = json.loads(sys.stdin.read())
    technique = rebuild(data["technique"])
    result = b.SynthesizeCode(
        request=data["request"],
        technique=technique,
    )
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
