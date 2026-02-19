function DecomposeProblem(request: string) -> ProcgenProblem {
  client Haiku
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
  client Haiku
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
  client Haiku
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

function SynthesizeCode(request: string, technique: TechniqueCard) -> SynthesizedCode {
  client Haiku
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

    RULES:
    - Output a single complete Python file that runs standalone
    - Use the technique's implementation pattern, not random-retry
    - Include a main() that demonstrates the generator with a printed example
    - Keep it under 150 lines

    {{ ctx.output_format }}
  "#
}

function VerifyTechnique(code: string, technique_name: string, fingerprint_imports: string[], fingerprint_patterns: string[], anti_patterns: string[]) -> TechniqueVerification {
  client Haiku
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
