from enum import Enum
from pydantic import BaseModel, Field


class OutputType(str, Enum):
    GRID_2D = "GRID_2D"
    GRAPH = "GRAPH"
    TREE = "TREE"
    SEQUENCE = "SEQUENCE"
    MESH_3D = "MESH_3D"


class ConstraintType(str, Enum):
    CONNECTIVITY = "CONNECTIVITY"
    PLACEMENT = "PLACEMENT"
    ORDERING = "ORDERING"
    DISTRIBUTION = "DISTRIBUTION"
    ADJACENCY = "ADJACENCY"
    STRUCTURAL = "STRUCTURAL"


class Constraint(BaseModel):
    name: str = ""
    type: ConstraintType = ConstraintType.STRUCTURAL
    description: str = ""


class ProcgenProblem(BaseModel):
    output_structure: OutputType = OutputType.GRID_2D
    constraints: list[Constraint] = []
    scale: str = "medium"
    realtime: bool = False


class SourceCategory(str, Enum):
    ACADEMIC = "ACADEMIC"
    OFFICIAL_DOCS = "OFFICIAL_DOCS"
    TUTORIAL = "TUTORIAL"
    BLOG_REPUTABLE = "BLOG_REPUTABLE"
    BLOG_UNKNOWN = "BLOG_UNKNOWN"
    FORUM = "FORUM"
    GENERATED = "GENERATED"


class Freshness(str, Enum):
    CURRENT = "CURRENT"
    DATED = "DATED"
    STALE = "STALE"
    TIMELESS = "TIMELESS"


class Source(BaseModel):
    url: str = ""
    domain: str = ""
    title: str = ""
    category: SourceCategory = SourceCategory.TUTORIAL
    freshness: Freshness = Freshness.CURRENT
    signals: list[str] = []
    should_use: bool = False


class Tradeoff(BaseModel):
    pro: str = ""
    con: str = ""


class Implementation(BaseModel):
    language: str = "python"
    dependencies: list[str] = []
    pattern: str = Field(default="", description="short pseudocode or code sketch, max 30 lines")
    complexity: str = "moderate"


class SourceRef(BaseModel):
    url: str = ""
    category: SourceCategory = SourceCategory.TUTORIAL
    accessed: str = ""


class Fingerprint(BaseModel):
    imports: list[str] = []
    file_artifacts: list[str] = []
    patterns: list[str] = []


class TechniqueCard(BaseModel):
    name: str = ""
    category: list[str] = []
    problem_types: list[OutputType] = []
    constraint_types: list[ConstraintType] = []
    description: str = ""
    tradeoffs: list[Tradeoff] = []
    implementation: Implementation = Implementation()
    sources: list[SourceRef] = []
    fingerprint: Fingerprint = Fingerprint()
    anti_patterns: list[str] = []
    syntax_notes: list[str] = []
    confidence: str = ""


class TechniqueVerification(BaseModel):
    uses_technique: bool = False
    evidence: list[str] = []
    anti_patterns_found: list[str] = []
    defaulted_to: str = ""


class SynthesizedCode(BaseModel):
    code: str = Field(default="", description="complete runnable Python file")
    imports: list[str] = Field(default=[], description="pip package names required")


class RefinementError(BaseModel):
    attempt: int = 0
    error_type: str = ""
    error_message: str = ""
    error_line: str = ""
    traceback: str = ""


class WardenVerdict(BaseModel):
    approved: bool = False
    repeated_errors: list[str] = []
    hallucinated_fixes: list[str] = []
    api_issues: list[str] = []
    notes: str = ""


class LazyVerdict(BaseModel):
    degenerate: bool = False
    reason: str = ""
