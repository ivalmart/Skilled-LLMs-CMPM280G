import sys
import json
import _log
from llm import call
from _types import ProcgenProblem


def main():
    request = sys.argv[1]
    _log.haiku("DecomposeProblem")
    prompt = f"""Analyze this procedural generation request and decompose it into a structured problem.

Request: {request}

Identify:
- The output structure type (GRID_2D, GRAPH, TREE, SEQUENCE, MESH_3D)
- All constraints (CONNECTIVITY, PLACEMENT, ORDERING, DISTRIBUTION, ADJACENCY, STRUCTURAL)
- The scale (small/medium/large)
- Whether it needs to run in realtime"""
    try:
        result = call(prompt, ProcgenProblem)
    except Exception as e:
        _log.fail(f"LLM call failed: {type(e).__name__}: {e}")
        sys.exit(1)
    d = result.model_dump()
    _log.detail(f"-> {d['output_structure']}, {len(d['constraints'])} constraints")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
