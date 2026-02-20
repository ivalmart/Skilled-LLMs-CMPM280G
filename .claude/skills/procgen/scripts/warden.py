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
Determine if the refinement actually fixes the errors, is cosmetic, or introduces API problems.

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
- Check library API usage: wrong keyword args, incorrect function signatures, misused return values, deprecated calls. List each in api_issues.
- Check for obvious syntax errors targeting the library (e.g. calling nonexistent methods, wrong arg types, missing required params). Include those in api_issues too.
- Check whether the original errors are truly fixed or just worked around (e.g. wrapping in try/except, catching and ignoring, or removing the code that caused the error). Workarounds count as hallucinated_fixes.
- Set approved to true ONLY if real substantive fixes were made, API usage is correct, and errors are genuinely addressed.
- Set approved to false if changes are cosmetic, errors are worked around, or api_issues are found.

Return ONLY a JSON object, no other text."""

    try:
        verdict = call(prompt, WardenVerdict)
    except Exception as e:
        _log.fail(f"LLM call failed: {type(e).__name__}")
        sys.exit(1)
    d = verdict.model_dump()
    if d.get("approved"):
        _log.ok("approved")
        print(json.dumps(d, indent=2))
        return
    issues = d.get("api_issues", [])
    if issues:
        _log.fail(f"rejected (api issues: {', '.join(issues[:3])})")
    else:
        _log.fail(f"rejected: {d.get('notes', '')}")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
