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
        
        i = 1
        while i < len(lines):
            line = lines[i]
            m = re.match(r"^- (\w[\w_]*): (.+)$", line)
            if not m:
                i += 1
                continue
            
            key, val = m.group(1), m.group(2)
            
            # Handle YAML block scalars (|)
            if val.strip() == "|":
                block_lines = []
                i += 1
                # Capture indented lines that follow
                while i < len(lines) and (lines[i].startswith("  ") or lines[i].strip() == ""):
                    if lines[i].startswith("  "):
                        block_lines.append(lines[i][2:])  # remove 2-space indent
                    i += 1
                val = "\n".join(block_lines).rstrip()
                i -= 1  # back up one since loop will increment
            
            # Process based on field type
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
            
            i += 1
        
        techniques.append(fields)
    return techniques


def problem_text(problem):
    parts = [problem.get("output_structure", "")]
    for c in problem.get("constraints", []):
        if isinstance(c, dict):
            parts.append(c.get("type", ""))
            parts.append(c.get("description", ""))
        else:
            parts.append(str(c))
    parts.append(problem.get("scale", ""))
    return " ".join(p for p in parts if p)


def technique_text(t):
    parts = [t.get("name", "")]
    parts.extend(t.get("problem_types", []))
    parts.extend(t.get("constraint_types", []))
    parts.append(t.get("description", ""))
    return " ".join(p for p in parts if p)


def lookup(problem):
    techniques = load()
    if not techniques:
        _log.detail("technique memory is empty")
        return []
    _log.detail(f"{len(techniques)} techniques in memory")

    from sentence_transformers import SentenceTransformer
    import numpy as np

    model = SentenceTransformer("all-MiniLM-L6-v2")
    query = problem_text(problem)
    _log.detail(f"query: {query[:80]}")
    q_emb = model.encode(query)

    texts = [technique_text(t) for t in techniques]
    t_embs = model.encode(texts)

    scored = []
    for i, t in enumerate(techniques):
        raw = float(np.dot(q_emb, t_embs[i]) / (np.linalg.norm(q_emb) * np.linalg.norm(t_embs[i]) + 1e-8))
        raw = max(raw, 0.0)
        notes = t.get("syntax_notes", [])
        penalty = min(len(notes) * 0.1, 0.8)
        score = raw * (1.0 - penalty)
        _log.detail(f"  {t.get('name', '?')}: sim={raw:.3f} notes={len(notes)} score={score:.3f}")
        scored.append((score, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, "technique": t} for s, t in scored[:5]]


def save(card):
    TECHNIQUES_PATH.parent.mkdir(parents=True, exist_ok=True)
    tradeoffs = "; ".join(
        f"{t['pro']} / {t['con']}" for t in card.get("tradeoffs", [])
    )
    lines = [f"## {card['name']}\n"]
    for key in ("problem_types", "constraint_types", "description", "tradeoffs",
                "implementation_language", "implementation_dependencies",
                "implementation_pattern", "implementation_complexity",
                "sources", "fingerprint_imports", "fingerprint_artifacts",
                "fingerprint_patterns", "anti_patterns", "syntax_notes",
                "confidence"):
        val = card.get(key)
        if not val:
            continue
        if key == "tradeoffs":
            lines.append(f"- {key}: {tradeoffs}\n")
        elif key == "implementation_pattern":
            val_str = str(val).strip()
            if "\n" in val_str:
                lines.append(f"- {key}: |\n")
                for line in val_str.split("\n"):
                    lines.append(f"  {line}\n")
            else:
                lines.append(f"- {key}: {val_str}\n")
        elif isinstance(val, list):
            lines.append(f"- {key}: {', '.join(str(v) for v in val)}\n")
        else:
            lines.append(f"- {key}: {val}\n")
    content = "".join(lines)
    try:
        existing = TECHNIQUES_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        existing = ""
    if card['name'] in existing:
        pattern = rf"## {re.escape(card['name'])}.*?(?=\n## |\Z)"
        existing = re.sub(pattern, content.rstrip(), existing, flags=re.DOTALL)
    else:
        existing += "\n" + content
    TECHNIQUES_PATH.write_text(existing, encoding="utf-8")


def annotate(card_name, notes):
    techniques = load()
    for t in techniques:
        if t.get("name") == card_name:
            existing = set(t.get("syntax_notes", []))
            for note in notes:
                if note not in existing:
                    existing.add(note)
            t["syntax_notes"] = sorted(list(existing))
            save(t)
            _log.detail(f"annotated '{card_name}' with {len(notes)} notes")
            _log.detail(f"saved {len(existing)} syntax notes")
            return
    _log.fail(f"technique '{card_name}' not found")


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
        annotate(data.get("technique_name", ""), data.get("syntax_notes", []))
        print(json.dumps({"status": "annotated"}))


if __name__ == "__main__":
    main()
