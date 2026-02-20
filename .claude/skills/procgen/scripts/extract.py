import sys
import json
import _log
from llm import call
from _types import TechniqueCard


def main():
    data = json.loads(sys.stdin.read())
    problem = data["problem"]
    constraints = ", ".join(
        f"{c['name']} ({c['type']})" for c in problem.get("constraints", [])
    )
    _log.haiku("ExtractTechnique")
    prompt = f"""Extract a procedural generation technique from this source content.

Source URL: {data["url"]}
Source content (may be truncated):
{data["content"]}

The technique should be relevant to this problem:
- Output structure: {problem["output_structure"]}
- Constraints: {constraints}
- Scale: {problem["scale"]}

Extract:
- The technique name and category
- Which problem types and constraint types it handles
- Tradeoffs (pros and cons)
- Implementation details (language, dependencies, a short code pattern)
- A fingerprint for verification (imports, file artifacts, code patterns that indicate this technique is being used)
- Anti-patterns (code patterns that indicate the model fell back to generate-and-test instead of using this technique)"""
    try:
        result = call(prompt, TechniqueCard)
    except Exception as e:
        _log.fail(f"LLM call failed: {type(e).__name__}")
        sys.exit(1)
    d = result.model_dump()
    _log.detail(f"-> {d.get('name', '?')}")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
