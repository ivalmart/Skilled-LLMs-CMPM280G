# Design Fiction: The Procgen Knowledge System

## Session 1 — Cold Start

Ava opens Claude Code in a new project. She types:

> "Write me a dungeon generator. 10x10 grid, walls, a gem, an altar. The player
> must be able to reach the gem before the altar. Visualize it in the terminal."

The system has no memory. The memory file is empty. A **PreToolUse hook** on
Write/Edit fires before any code is generated. It invokes the
**problem-decomposer** skill.

### Stage 1: Problem Decomposition (Haiku + BAML)

The skill sends Ava's request through a BAML function:

```baml
class ProcgenProblem {
  output_structure  OutputType
  constraints       Constraint[]
  scale             string
  realtime          bool
}

enum OutputType {
  GRID_2D
  GRAPH
  TREE
  SEQUENCE
  MESH_3D
}

class Constraint {
  name        string
  type        ConstraintType
  description string
}

enum ConstraintType {
  CONNECTIVITY
  PLACEMENT
  ORDERING
  DISTRIBUTION
  ADJACENCY
  STRUCTURAL
}
```

Haiku returns (reliably, because SAP catches its formatting mistakes):

```json
{
  "output_structure": "GRID_2D",
  "constraints": [
    {"name": "walls", "type": "STRUCTURAL", "description": "walls placed on grid"},
    {"name": "reachability", "type": "CONNECTIVITY", "description": "path must exist between start, gem, altar, exit"},
    {"name": "visit_order", "type": "ORDERING", "description": "gem must be visited before altar"}
  ],
  "scale": "small",
  "realtime": false
}
```

### Stage 2: Memory Lookup

The system checks its memory. Empty. Nothing relevant. Proceeds to web search.

### Stage 3: Technique Discovery (Jina + Haiku + BAML)

The system needs to find *what techniques exist* for this type of problem. It
doesn't know yet. It constructs a search query from the decomposed problem:

    "procedural generation 2D grid constraints connectivity placement"

It searches via Jina's search endpoint. Results come back. But before
using any of them, the **source-verifier** runs.

### Stage 3.5: Source Verification

This is its own BAML function:

```baml
class Source {
  url           string
  domain        string
  category      SourceCategory
  freshness     Freshness
  signals       string[]
}

enum SourceCategory {
  ACADEMIC       @description("arxiv, ACM, IEEE, university pages")
  OFFICIAL_DOCS  @description("library/framework official documentation")
  TUTORIAL       @description("structured tutorial from known platform")
  BLOG_REPUTABLE @description("blog from known practitioner or organization")
  BLOG_UNKNOWN   @description("blog from unknown author, no citations")
  FORUM          @description("stackoverflow, reddit, discord")
  GENERATED      @description("appears AI-generated, no clear author")
}

enum Freshness {
  CURRENT    @description("within 2 years or for stable algorithm")
  DATED      @description("2-5 years, may have outdated deps")
  STALE      @description("5+ years, likely outdated implementations")
  TIMELESS   @description("mathematical/algorithmic, age irrelevant")
}
```

Jina returned 5 results. The verifier classifies them:

| # | URL | Category | Freshness | Use? |
|---|-----|----------|-----------|------|
| 1 | arxiv.org/abs/... (Smith 2018, ASP for level design) | ACADEMIC | TIMELESS | yes |
| 2 | roguebasin.com/WFC_tutorial | TUTORIAL | CURRENT | yes |
| 3 | medium.com/random-blogger/my-dungeon-gen | BLOG_UNKNOWN | DATED | skip |
| 4 | github.com/mxgmn/WaveFunctionCollapse | OFFICIAL_DOCS | CURRENT | yes |
| 5 | potassco.org/clingo/getting-started | OFFICIAL_DOCS | CURRENT | yes |

Sources 1, 2, 4, 5 pass. Source 3 is skipped — unknown blog, no citations.

The system fetches the passing sources through Jina Reader
(`r.jina.ai/<url>` → markdown).

### Stage 4: Technique Extraction (Haiku + BAML)

Another BAML function runs over each fetched document:

```baml
class TechniqueCard {
  name              string
  category          string[]
  problem_types     OutputType[]
  constraint_types  ConstraintType[]
  description       string
  tradeoffs         Tradeoff[]
  implementation    Implementation
  source            SourceRef
}

class Tradeoff {
  pro   string
  con   string
}

class Implementation {
  language    string
  dependency  string[]
  pattern     string    @description("short pseudocode or code sketch, max 30 lines")
  complexity  string
}

class SourceRef {
  url       string
  category  SourceCategory
  accessed  string
}
```

From the 4 sources, Haiku extracts technique cards. These are structured,
typed, inspectable objects — not raw text.

### Stage 5: Write to Memory

The system now has 3 technique cards it didn't have before: ASP for level
design, WFC, and BSP with constraint validation.

It writes them to its memory file. Not as prose — as structured entries that
can be parsed later:

```markdown
## Techniques

### ASP (Answer Set Programming)
- problem_types: GRID_2D, GRAPH
- constraint_types: CONNECTIVITY, PLACEMENT, ORDERING, ADJACENCY
- tradeoffs: guarantees all constraints satisfied; requires clingo dependency
- source: arxiv.org/abs/..., potassco.org, accessed 2026-02-15
- confidence: high (ACADEMIC + OFFICIAL_DOCS, cross-referenced)

### WFC (Wave Function Collapse)
- problem_types: GRID_2D, MESH_3D
- constraint_types: ADJACENCY, STRUCTURAL
- tradeoffs: fast and visual; cannot enforce global path constraints easily
- source: github.com/mxgmn/WaveFunctionCollapse, accessed 2026-02-15
- confidence: high (OFFICIAL_DOCS)
```

### Stage 6: Technique Selection

Now the system matches the problem decomposition against its (newly populated)
memory. The problem has CONNECTIVITY + ORDERING constraints on a GRID_2D.

- ASP: supports CONNECTIVITY, ORDERING on GRID_2D. Strong match.
- WFC: supports ADJACENCY on GRID_2D, but not ORDERING. Weak match.

ASP is selected. The system already has the technique card including
implementation patterns from the fetched sources.

### Stage 7: Code Synthesis

The main model (typically something small) receives:

- The original request
- The structured problem decomposition
- The ASP technique card — which includes **runnable code**, not descriptions:
  - A minimal `.lp` file showing clingo rules for grid constraints
  - A 3-line Python snippet showing `subprocess.run(['clingo', ...])` integration
  - The technique's **verification fingerprint**

The technique card includes:

```markdown
fingerprint:
  imports: ["subprocess"] or ["clingo"]
  file_artifacts: ["*.lp"]
  patterns: ["#show", ":-", ":- not"]
anti_patterns:
  - "random.randint" with retry loop = generate-and-test, NOT ASP
  - "while attempts < " = brute force, NOT constraint solving
```

The model adapts the working code example to Ava's specific requirements.
It doesn't need to invent clingo syntax from a textbook description — it
modifies a working example.

### Stage 8: PostToolUse Verification Hook

After the model writes code, a **PostToolUse hook** fires. It sends the
generated code + the technique card to a BAML verification function (Haiku):

```baml
class TechniqueVerification {
  uses_technique  bool
  evidence        string[]
  anti_patterns   string[]  @description("detected anti-patterns from the technique card")
  defaulted_to    string    @description("what the model fell back to, if not the technique")
}
```

Haiku checks:
- Does the code contain the fingerprint signals? (`import subprocess`, `.lp` file, `:-` rules)
- Does it contain anti-patterns? (`while attempts < 1000`, `random.randint` retry loops)

If verification fails — the model wrote generate-and-test with ASP comments
(exactly what happened in Session 0) — the hook **rejects the code** and
re-prompts with:

> "You selected ASP but wrote generate-and-test. Here is the working clingo
> integration from the technique card: [code]. Rewrite using this pattern."

The retry has the concrete code example front and center, not a textbook
explanation.

### Stage 9: The Hook Closes

The PostToolUse hook sees verification passed. Code is written.
The user sees not just the code but the decision trail:

> Problem type: 2D grid with connectivity + ordering constraints
> Technique selected: ASP (via clingo)
> Sources consulted: [arxiv, potassco.org] (confidence: high)
> Memory updated: 3 new techniques indexed

---

## Session 7 — Warm Memory

It's a week later. Ava types:

> "I need a terrain generator. Heightmap with realistic erosion, rivers that
> flow downhill, biome placement based on elevation and moisture."

### What's different now

Memory has been growing. Over 6 previous sessions, the system has encountered
and indexed 14 techniques. The problem-decomposer runs:

```json
{
  "output_structure": "GRID_2D",
  "constraints": [
    {"name": "physical_realism", "type": "STRUCTURAL", "description": "erosion simulation"},
    {"name": "flow_direction", "type": "CONNECTIVITY", "description": "rivers flow downhill"},
    {"name": "biome_mapping", "type": "DISTRIBUTION", "description": "elevation + moisture → biome"}
  ],
  "scale": "large",
  "realtime": false
}
```

The system checks memory. It finds:

- **Perlin noise** (indexed in session 3, terrain tutorial) — matches GRID_2D + STRUCTURAL
- **Hydraulic erosion** (indexed in session 5, academic paper) — matches STRUCTURAL
- **Diamond-square** (indexed in session 3) — matches GRID_2D but weaker fit

It already has technique cards for Perlin noise and diamond-square. But
hydraulic erosion was only partially indexed — the source was a blog post
(BLOG_REPUTABLE, from a recognized game dev) and the implementation pattern
was incomplete.

### Selective web fetch

The system doesn't re-fetch everything. It only fetches what's missing:
a better implementation reference for hydraulic erosion. It searches,
verifies the source (finds a Sebastian Lague tutorial — TUTORIAL, CURRENT),
extracts the technique card, and **updates** the memory entry.

The old entry is not deleted — it's versioned. The memory now tracks:

```markdown
### Hydraulic Erosion
- ...
- source_history:
  - gamasutra.com/blog/..., accessed 2026-02-10 (BLOG_REPUTABLE)
  - youtube.com/SebastianLague/..., accessed 2026-02-17 (TUTORIAL)
- confidence: high (multiple independent sources agree)
```

### Composition

This problem needs *multiple* techniques composed together. The system
recommends a pipeline:

1. Perlin noise → base heightmap
2. Hydraulic erosion simulation → realistic terrain
3. Moisture map (another Perlin layer) → biome classification

Each step has a technique card. The code synthesizer composes them.

---

## Session 31 — Memory Gets Large

Ava's project has been running for two months. Memory now contains 47
technique entries, 12 source verification records, and cross-references
between techniques.

The memory file is 15,000 lines.

### The RLM Kicks In

When the problem-decomposer needs to search memory, it can no longer fit the
whole file in context. The system uses the RLM pattern:

1. The memory file is chunked (it's already structured with markdown headers,
   so semantic chunking is natural)
2. A Haiku sub-call scans each chunk for techniques matching the current
   problem decomposition
3. Matching technique cards are returned to the main context
4. Only relevant techniques enter the code synthesis stage

This is the same RLM pattern from the first attempt — but now it's searching
a *structured, verified, self-built* knowledge base instead of a raw
textbook chapter.

### Memory Maintenance

Over time, some entries become stale:

- A library changed its API (the `clingo` Python bindings were updated)
- A technique turned out to be impractical (a paper's approach didn't scale)
- Two entries describe the same technique with different names

A periodic **memory-gardener** agent (or a hook on SessionStart) can:

- Check if source URLs are still live
- Flag entries older than N months for re-verification
- Merge duplicate entries
- Prune techniques that were never selected

---

## Session 31, Alternate — Encountering Bad Information

Ava asks for a city road network generator. The system searches the web and
one of the returned sources is a blog post that claims:

> "L-systems are the best approach for road networks because they can model
> any branching pattern with just 3 rules."

The source-verifier classifies it as BLOG_UNKNOWN. But the system has a
secondary check: **cross-referencing**.

It searches for "L-systems road network generation" and finds:

1. An academic paper (Parish & Muller 2001) that *does* use L-systems for
   road networks — but notes they struggle with global constraints like
   connectivity to existing infrastructure
2. A more recent paper that uses tensor fields instead, citing L-systems'
   limitations

The system writes the technique card with a nuance:

```markdown
### L-systems for Road Networks
- problem_types: GRAPH, GRID_2D
- constraint_types: STRUCTURAL
- tradeoffs:
  - pro: elegant branching patterns, compact rule sets
  - con: poor at global constraints (connectivity to existing roads)
  - con: cited as limited by tensor field approaches (Chen 2015)
- source: Parish & Muller 2001 (ACADEMIC, TIMELESS), blog.example.com (BLOG_UNKNOWN, discounted)
- confidence: medium (technique is real but has known limitations)
```

The blog wasn't wrong — L-systems *can* generate road networks. But the system
captured the nuance that the blog missed.

---

## The Architecture, Summarized

```
Session starts
      │
      ▼
User request → PreToolUse hook intercepts before code generation
      │
      ▼
Problem Decomposer (BAML + Haiku)
      │ typed ProcgenProblem struct
      ▼
Memory Lookup
      │
      ├── HIT: technique cards found in memory
      │     │
      │     ▼
      │   Are they fresh? Sources still valid?
      │     │
      │     ├── YES → use them
      │     └── NO → selective web fetch for updates
      │
      └── MISS: nothing in memory matches
            │
            ▼
      Web Search (Jina search → Jina reader)
            │ raw markdown
            ▼
      Source Verifier (BAML + Haiku)
            │ classified, scored sources
            ▼
      Technique Extractor (BAML + Haiku)
            │ typed TechniqueCard structs
            ▼
      Write to Memory (append, versioned)
            │
            ▼
Technique Selection (match problem → techniques)
      │
      ▼
Code Synthesis (main model writes generator)
      │
      ▼
Memory grows. Eventually, RLM is needed to search it.
```

**Nothing is manually curated.** The memory starts empty and fills itself.
**Nothing is a black box.** Every stage produces typed, inspectable output.
**Coverage gaps are explicit.** If memory has nothing and web search finds
nothing reputable, the system says so rather than guessing.
