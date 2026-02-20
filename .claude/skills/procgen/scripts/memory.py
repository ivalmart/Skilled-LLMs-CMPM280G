import sys
import json
import re
from pathlib import Path

import _log

TECHNIQUES_PATH = Path(__file__).resolve().parents[2] / "knowledge" / "techniques.md"


def load():
    if not TECHNIQUES_PATH.exists():
        return []
    text = TECHNIQUES_PATH.read_text(encoding="utf-8")
    sections = re.split(r"\n(?=## )", text.strip())
    techniques = []
    for section in sections:
        if not section.startswith("## "):
            continue
        lines = section.strip().split("\n")
        name = lines[0].removeprefix("## ").strip()
        fields = {"name": name}
        for line in lines[1:]:
            m = re.match(r"^- (\w[\w_]*): (.+)$", line)
            if not m:
                continue
            key, val = m.group(1), m.group(2)
            if key in ("problem_types", "constraint_types", "fingerprint_imports",
                        "fingerprint_artifacts", "fingerprint_patterns",
                        "anti_patterns", "implementation_dependencies",
                        "syntax_notes"):
                fields[key] = [v.strip() for v in val.split(",")]
            elif key == "tradeoffs":
                fields[key] = []
                for pair in val.split(";"):
                    parts = pair.strip().split("/")
                    if len(parts) == 2:
                        fields[key].append({"pro": parts[0].strip(), "con": parts[1].strip()})
            else:
                fields[key] = val
        techniques.append(fields)
    return techniques


def lookup(problem):
    techniques = load()
    if not techniques:
        _log.detail("technique memory is empty")
        return []
    _log.detail(f"{len(techniques)} techniques in memory")
    target_types = {problem.get("output_structure", "")}
    target_constraints = set()
    for c in problem.get("constraints", []):
        if isinstance(c, dict):
            target_constraints.add(c.get("type", ""))
        else:
            target_constraints.add(str(c))
    scored = []
    for t in techniques:
        ptypes = set(t.get("problem_types", []))
        ctypes = set(t.get("constraint_types", []))
        overlap = len(ptypes & target_types) + len(ctypes & target_constraints)
        total = max(len(target_types) + len(target_constraints), 1)
        scored.append((overlap / total, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, "technique": t} for s, t in scored[:5]]


def save(card):
    TECHNIQUES_PATH.parent.mkdir(parents=True, exist_ok=True)
    tradeoffs = "; ".join(
        f"{t['pro']} / {t['con']}" for t in card.get("tradeoffs", [])
    )
    sources = ", ".join(
        f"{s['url']} ({s.get('category', '')}, {s.get('accessed', '')})"
        for s in card.get("sources", [])
    )
    impl = card.get("implementation", {})
    fp = card.get("fingerprint", {})
    block = f"""
## {card["name"]}
- problem_types: {", ".join(card.get("problem_types", []))}
- constraint_types: {", ".join(card.get("constraint_types", []))}
- description: {card.get("description", "")}
- tradeoffs: {tradeoffs}
- implementation_language: {impl.get("language", "")}
- implementation_dependencies: {", ".join(impl.get("dependencies", []))}
- implementation_pattern: |
    {impl.get("pattern", "").replace(chr(10), chr(10) + "    ")}
- implementation_complexity: {impl.get("complexity", "")}
- sources: {sources}
- fingerprint_imports: {", ".join(fp.get("imports", []))}
- fingerprint_artifacts: {", ".join(fp.get("file_artifacts", []))}
- fingerprint_patterns: {", ".join(fp.get("patterns", []))}
- anti_patterns: {", ".join(card.get("anti_patterns", []))}
- syntax_notes: {", ".join(card.get("syntax_notes", []))}
- confidence: {card.get("confidence", "")}
"""
    with open(TECHNIQUES_PATH, "a", encoding="utf-8") as f:
        f.write(block)
    _log.ok(f"saved: {card['name']}")


def annotate(data):
    if not TECHNIQUES_PATH.exists():
        return
    text = TECHNIQUES_PATH.read_text(encoding="utf-8")
    name = data.get("technique_name", "")
    new_notes = data.get("syntax_notes", [])
    if not name or not new_notes:
        return

    pattern = rf"(## {re.escape(name)}\n)(.*?)(?=\n## |\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        _log.fail(f"technique '{name}' not found for annotation")
        return

    section = match.group(0)
    notes_match = re.search(r"^- syntax_notes: (.+)$", section, re.MULTILINE)
    if notes_match:
        existing = [n.strip() for n in notes_match.group(1).split(",")]
        merged = list(dict.fromkeys(existing + new_notes))
        updated = section.replace(notes_match.group(0), f"- syntax_notes: {', '.join(merged)}")
    else:
        anti_match = re.search(r"^(- anti_patterns: .+)$", section, re.MULTILINE)
        if anti_match:
            updated = section.replace(
                anti_match.group(0),
                f"{anti_match.group(0)}\n- syntax_notes: {', '.join(new_notes)}",
            )
        else:
            updated = section + f"\n- syntax_notes: {', '.join(new_notes)}"

    text = text[:match.start()] + updated + text[match.end():]
    TECHNIQUES_PATH.write_text(text, encoding="utf-8")
    _log.ok(f"annotated '{name}' with {len(new_notes)} notes")


def main():
    action = sys.argv[1]
    data = json.loads(sys.stdin.read())
    if action == "lookup":
        print(json.dumps(lookup(data), indent=2))
        return
    if action == "save":
        save(data)
        print(json.dumps({"status": "saved"}))
        return
    if action == "annotate":
        annotate(data)
        print(json.dumps({"status": "annotated"}))


if __name__ == "__main__":
    main()
