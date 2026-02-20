function DecomposeProblem(request: string) -> ProcgenProblem {
  client SMALL_MODEL
  prompt #"
    Analyze this procedural generation request and decompose it into a structured problem.

    Request: {{ request }}

    Identify:
    - The output structure type (grid, graph, tree, sequence, mesh)
    - All constraints (connectivity, placement, ordering, distribution, adjacency, structural)
    - The scale (small/medium/large)
    - Whether it needs to run in realtime

    {{ ctx.output_format }}
  "#
}

function VerifySource(url: string, title: string, snippet: string) -> Source {
  client SMALL_MODEL
  prompt #"
    Evaluate this web source for reliability as a procedural generation reference.

    URL: {{ url }}
    Title: {{ title }}
    Snippet: {{ snippet }}

    Classify the source category, freshness, and whether it should be used.
    Set should_use to false for AI-generated content, unknown blogs without citations, or stale implementations.

    {{ ctx.output_format }}
  "#
}

function ExtractTechnique(content: string, url: string, problem: ProcgenProblem) -> TechniqueCard {
  client SMALL_MODEL
  prompt #"
    Extract a procedural generation technique from this source content.

    Source URL: {{ url }}
    Source content (may be truncated):
    {{ content }}

    The technique should be relevant to this problem:
    - Output structure: {{ problem.output_structure }}
    - Constraints: {% for c in problem.constraints %}{{ c.name }} ({{ c.type }}){% if not loop.last %}, {% endif %}{% endfor %}
    - Scale: {{ problem.scale }}

    Extract:
    - The technique name and category
    - Which problem types and constraint types it handles
    - Tradeoffs (pros and cons)
    - Implementation details (language, dependencies, a short code pattern)
    - A fingerprint for verification (imports, file artifacts, code patterns that indicate this technique is being used)
    - Anti-patterns (code patterns that indicate the model fell back to generate-and-test instead of using this technique)

    {{ ctx.output_format }}
  "#
}

function SynthesizeCode(request: string, technique: TechniqueCard, syntax_notes: string[]) -> SynthesizedCode {
  client SMALL_MODEL
  prompt #"
    Write a complete, runnable Python file that implements the following procedural generation request
    using the specified technique. Do NOT fall back to generate-and-test (random retry loops).

    Request: {{ request }}

    Technique: {{ technique.name }}
    Description: {{ technique.description }}
    Implementation pattern:
    {{ technique.implementation.pattern }}

    Required imports/fingerprint: {{ technique.fingerprint.imports }}
    Expected code patterns: {{ technique.fingerprint.patterns }}

    Constraints to satisfy:
    {% for ct in technique.constraint_types %}
    - {{ ct }}
    {% endfor %}

    {% if syntax_notes %}
    Known syntax pitfalls for this technique (learned from prior runs):
    {% for note in syntax_notes %}
    - {{ note }}
    {% endfor %}
    {% endif %}

    RULES:
    - Output a single complete Python file that runs standalone
    - Use the technique's implementation pattern, not random-retry
    - Include a main() that demonstrates the generator with a printed example
    - Keep it under 150 lines

    {{ ctx.output_format }}
  "#
}

function RefineCode(request: string, technique: TechniqueCard, broken_code: string, errors: RefinementError[], syntax_notes: string[]) -> SynthesizedCode {
  client SMALL_MODEL
  prompt #"
    Fix this broken procedural generation code. The previous attempt failed at runtime.

    Request: {{ request }}
    Technique: {{ technique.name }}
    Implementation pattern: {{ technique.implementation.pattern }}

    Broken code:
    {{ broken_code }}

    Errors encountered:
    {% for e in errors %}
    Attempt {{ e.attempt }}: {{ e.error_type }} — {{ e.error_message }}
    Line: {{ e.error_line }}
    Traceback: {{ e.traceback }}
    {% endfor %}

    {% if syntax_notes %}
    Known syntax issues for this technique (from prior runs):
    {% for note in syntax_notes %}
    - {{ note }}
    {% endfor %}
    {% endif %}

    RULES:
    - Fix the actual errors, don't just rename variables or add comments
    - Keep using the technique's implementation pattern
    - Output a complete runnable Python file
    - Keep it under 150 lines

    {{ ctx.output_format }}
  "#
}

function WatchRefinement(original_code: string, refined_code: string, errors: RefinementError[], warden_notes: string) -> WardenVerdict {
  client SMALL_MODEL
  prompt #"
    You are a code review warden. Compare the original broken code with the refined version.
    Your job: verify the refinement actually fixes the errors, not just cosmetic changes.

    Original (broken) code:
    {{ original_code }}

    Refined code:
    {{ refined_code }}

    Errors the refinement should fix:
    {% for e in errors %}
    - {{ e.error_type }}: {{ e.error_message }} (line: {{ e.error_line }})
    {% endfor %}

    {% if warden_notes %}
    Notes from prior warden rejections:
    {{ warden_notes }}
    {% endif %}

    CHECK:
    1. Did the refined code actually change the lines that caused the errors?
       If the same error-causing patterns remain, list them in repeated_errors.
    2. Is the fix cosmetic only (renamed variable, added comment, reordered unchanged lines)?
       If structurally identical despite surface changes, list in hallucinated_fixes.
    3. Set approved=true ONLY if real, substantive fixes were made to address the errors.

    {{ ctx.output_format }}
  "#
}

function CheckLazy(request: string, technique_name: string, stdout: string) -> LazyVerdict {
  client SMALL_MODEL
  prompt #"
    You are checking if a procedural generator's output is degenerate.
    Degenerate means the code technically runs but produces minimal, trivial,
    or exploitative output that satisfies constraints by cheating.

    Request: {{ request }}
    Technique: {{ technique_name }}

    Program output:
    {{ stdout }}

    Examples of degenerate output:
    - A dungeon that is just a thin corridor hugging walls
    - A maze with no branching (single path)
    - A terrain that is completely flat except one spike
    - A level where all items cluster in one corner
    - A solver that hits the exact minimum constraint and stops

    Set degenerate=true if the output looks like it's gaming the constraints
    rather than producing genuinely interesting content. Explain why in reason.

    {{ ctx.output_format }}
  "#
}

function VerifyTechnique(code: string, technique_name: string, fingerprint_imports: string[], fingerprint_patterns: string[], anti_patterns: string[]) -> TechniqueVerification {
  client SMALL_MODEL
  prompt #"
    Verify that this code actually uses the recommended procedural generation technique.

    Technique: {{ technique_name }}

    Expected fingerprint imports: {{ fingerprint_imports }}
    Expected code patterns: {{ fingerprint_patterns }}
    Anti-patterns (indicate generate-and-test fallback): {{ anti_patterns }}

    Code to verify:
    {{ code }}

    Check if the code contains the expected fingerprint signals and whether it contains any anti-patterns.
    If it doesn't use the technique, identify what it defaulted to instead.

    {{ ctx.output_format }}
  "#
}
