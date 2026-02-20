import sys
import json
import _log
from llm import call
from _types import LazyVerdict


def main():
    data = json.loads(sys.stdin.read())
    _log.haiku("CheckLazy")

    prompt = f"""You are checking if a procedural generator's output is degenerate.
Degenerate means the code technically runs but produces minimal, trivial,
or exploitative output that satisfies constraints by cheating.

Request: {data["request"]}
Technique: {data["technique_name"]}

Program output:
{data["stdout"]}

Examples of degenerate output:
- A dungeon that is just a thin corridor hugging walls
- A maze with no branching (single path)
- A terrain that is completely flat except one spike
- A level where all items cluster in one corner
- A solver that hits the exact minimum constraint and stops

Set degenerate=true if the output looks like it's gaming the constraints
rather than producing genuinely interesting content. Explain why in reason."""

    try:
        verdict = call(prompt, LazyVerdict)
    except Exception as e:
        _log.fail(f"LLM call failed: {type(e).__name__}")
        sys.exit(1)
    d = verdict.model_dump()
    if d.get("degenerate"):
        _log.fail(f"degenerate: {d.get('reason', '')}")
    else:
        _log.ok("output looks genuine")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
