import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

import _log
from baml_client.sync_client import b
from baml_client.types import (
    TechniqueCard, Implementation, Fingerprint, SourceRef, Tradeoff,
    OutputType, ConstraintType, SourceCategory, RefinementError,
)


def rebuild(d):
    impl_data = d.get("implementation", d.get("implementation_pattern", {}))
    if isinstance(impl_data, str):
        impl_data = {"pattern": impl_data}
    impl_data.setdefault("language", "python")
    impl_data.setdefault("dependencies", [])
    impl_data.setdefault("complexity", "moderate")

    sources = []
    for s in d.get("sources", []):
        if isinstance(s, str):
            sources.append(SourceRef(url=s, category=SourceCategory("TUTORIAL"), accessed=""))
        else:
            sources.append(SourceRef(url=s.get("url", ""), category=SourceCategory(s.get("category", "TUTORIAL")), accessed=s.get("accessed", "")))

    fp = d.get("fingerprint", {})
    fp.setdefault("imports", [])
    fp.setdefault("file_artifacts", [])
    fp.setdefault("patterns", [])

    return TechniqueCard(
        name=d["name"],
        category=d.get("category", []),
        problem_types=[OutputType(p) for p in d.get("problem_types", [])],
        constraint_types=[ConstraintType(c) for c in d.get("constraint_types", [])],
        description=d.get("description", ""),
        tradeoffs=[Tradeoff(**t) for t in d.get("tradeoffs", [])],
        implementation=Implementation(**impl_data),
        sources=sources,
        fingerprint=Fingerprint(**fp),
        anti_patterns=d.get("anti_patterns", []),
        confidence=d.get("confidence", ""),
        syntax_notes=d.get("syntax_notes", []),
    )


def main():
    data = json.loads(sys.stdin.read())
    technique = rebuild(data["technique"])
    notes = data.get("syntax_notes", technique.syntax_notes or [])

    try:
        if "errors" in data:
            nerr = len(data["errors"])
            _log.haiku(f"RefineCode ({nerr} error{'s' if nerr != 1 else ''})")
            errors = [RefinementError(**e) for e in data["errors"]]
            result = b.RefineCode(
                request=data["request"],
                technique=technique,
                broken_code=data["broken_code"],
                errors=errors,
                syntax_notes=notes,
            )
        else:
            _log.haiku(f"SynthesizeCode ({technique.name})")
            result = b.SynthesizeCode(
                request=data["request"],
                technique=technique,
                syntax_notes=notes,
            )
    except Exception as e:
        _log.fail(f"BAML call failed: {type(e).__name__}")
        sys.exit(1)

    d = result.model_dump()
    lines = len(d.get("code", "").strip().split("\n"))
    _log.detail(f"-> {lines} lines")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
