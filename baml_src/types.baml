enum OutputType {
  GRID_2D
  GRAPH
  TREE
  SEQUENCE
  MESH_3D
}

enum ConstraintType {
  CONNECTIVITY
  PLACEMENT
  ORDERING
  DISTRIBUTION
  ADJACENCY
  STRUCTURAL
}

class Constraint {
  name string
  type ConstraintType
  description string
}

class ProcgenProblem {
  output_structure OutputType
  constraints Constraint[]
  scale string
  realtime bool
}

enum SourceCategory {
  ACADEMIC @description("arxiv, ACM, IEEE, university pages")
  OFFICIAL_DOCS @description("library/framework official documentation")
  TUTORIAL @description("structured tutorial from known platform")
  BLOG_REPUTABLE @description("blog from known practitioner or organization")
  BLOG_UNKNOWN @description("blog from unknown author, no citations")
  FORUM @description("stackoverflow, reddit, discord")
  GENERATED @description("appears AI-generated, no clear author")
}

enum Freshness {
  CURRENT @description("within 2 years or for stable algorithm")
  DATED @description("2-5 years, may have outdated deps")
  STALE @description("5+ years, likely outdated implementations")
  TIMELESS @description("mathematical/algorithmic, age irrelevant")
}

class Source {
  url string
  domain string
  title string
  category SourceCategory
  freshness Freshness
  signals string[]
  should_use bool
}

class Tradeoff {
  pro string
  con string
}

class Implementation {
  language string
  dependencies string[]
  pattern string @description("short pseudocode or code sketch, max 30 lines")
  complexity string
}

class SourceRef {
  url string
  category SourceCategory
  accessed string
}

class Fingerprint {
  imports string[]
  file_artifacts string[]
  patterns string[]
}

class TechniqueCard {
  name string
  category string[]
  problem_types OutputType[]
  constraint_types ConstraintType[]
  description string
  tradeoffs Tradeoff[]
  implementation Implementation
  sources SourceRef[]
  fingerprint Fingerprint
  anti_patterns string[]
  syntax_notes string[]
  confidence string
}

class TechniqueVerification {
  uses_technique bool
  evidence string[]
  anti_patterns_found string[]
  defaulted_to string
}

class SynthesizedCode {
  code string @description("complete runnable Python file implementing the generator")
  imports string[] @description("third-party packages required (pip install names)")
}

class RefinementError {
  attempt int
  error_type string
  error_message string
  error_line string
  traceback string
}

class WardenVerdict {
  approved bool
  repeated_errors string[]
  hallucinated_fixes string[]
  notes string
}

class LazyVerdict {
  degenerate bool
  reason string
}
