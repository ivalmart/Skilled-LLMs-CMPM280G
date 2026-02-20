import sys
import json
import _log
from llm import call
from _types import WardenVerdict


def main():
    data = json.loads(sys.stdin.read())
    _log.haiku("WatchRefinement")

    errors = data["errors"]
    err_lines = "\n".join(
        f"- {e.get('error_type', '')}: {e.get('error_message', '')} (line: {e.get('error_line', '')})"
        for e in errors
    )
    notes_block = ""
    prior = data.get("prior_notes", "")
    if prior:
        notes_block = f"\nNotes from prior warden rejections:\n{prior}\n"

    prompt = f"""Compare original broken code with the refined version.
Determine if the refinement actually fixes the errors or is just cosmetic.

Original (broken) code:
{data["original_code"]}

Refined code:
{data["refined_code"]}

Errors the refinement should fix:
{err_lines}
{notes_block}
Rules:
- If the same error-causing patterns remain unchanged, list them in repeated_errors.
- If the fix is cosmetic only (renamed variable, added comment, reordered unchanged lines), list in hallucinated_fixes.
- Set approved to true ONLY if real substantive fixes were made addressing the errors.
- Set approved to false if changes are cosmetic or errors are not addressed.

Return ONLY a JSON object, no other text."""

    try:
        verdict = call(prompt, WardenVerdict)
    except Exception as e:
        _log.fail(f"LLM call failed: {type(e).__name__}")
        sys.exit(1)
    d = verdict.model_dump()
    if d.get("approved"):
        _log.ok("approved")
    else:
        _log.fail(f"rejected: {d.get('notes', '')}")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
