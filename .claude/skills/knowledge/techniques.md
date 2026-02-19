
## Answer Set Programming (ASP)
- problem_types: GRID_2D, GRAPH
- constraint_types: CONNECTIVITY, PLACEMENT, DISTRIBUTION, ADJACENCY, STRUCTURAL
- description: ASP is a logic-programming approach that formulates procedural content generation as a constraint-solving problem. Game logic and mechanics are encoded in a Prolog-like language (AnsProlog), and constraints specify desired content properties. An ASP solver then finds content configurations that satisfy all declared constraints and logic rules.
- tradeoffs: Declarative specification of both game logic and constraints in a single unified language / Requires learning AnsProlog syntax and constraint formulation; steeper learning curve than constructive methods; Excellent for problems with many hard constraints that depend on game mechanics in complex ways / Computational performance scales poorly with problem size; may be impractical for large grids or complex domains; Guarantees solutions satisfy all constraints; no need for expensive fitness evaluation like search-based methods / Solver may timeout or return no solution if constraints are over-constrained or unsatisfiable; Easy to iteratively add, remove, or modify constraints based on generated content inspection / Requires deep understanding of game mechanics to correctly encode domain logic
- implementation_language: AnsProlog
- implementation_dependencies: Clingo, DLV, Smodels, or other ASP solver
- implementation_pattern: |
    % Facts: game constants
    max_grid(5).
    start((1,1)).
    
    % Game logic rules
    impassable(Tile) :- contains(Tile, wall).
    reachable(Tile) :- start(Tile).
    reachable(Next) :- reachable(Current), adjacent(Current, Next), not impassable(Next).
    
    % Content generation constraints
    {contains((X,Y), wall) : grid(X,Y)} = WallCount :- WallCount >= MinWalls, WallCount <= MaxWalls.
    
    % Hard constraints
    :- not reachable(gem_pos).
    :- not reachable(altar_pos).
    :- gem_pos = altar_pos.
    :- gem_pos = start(_).
    
    % Optimization (optional)
    #minimize{Distance : distance(gem_pos, altar_pos, Distance)}.
- implementation_complexity: NP-complete in general; practical complexity depends on constraint tightness and solver heuristics
- sources: C:\Users\jperr\Documents\CMPM280G\rlm\corpus\indexed\ASP.txt (ACADEMIC, 2024)
- fingerprint_imports: clingo, dlv, gringo
- fingerprint_artifacts: *.lp, *.asp, *.pl (AnsProlog dialect), solver output files, constraint specification files
- fingerprint_patterns: fact(:- .)., rule_head :- rule_body., :- integrity_constraint., {choice_variable} = constraint_expression., #minimize{...} or #maximize{...}, adj(X,Y) :- X=0..N, Y=0..M., reachable(Node) :- start(Node)., reachable(Next) :- reachable(Current), edge(Current, Next)., contains(Location, element) :- constraint logic., not predicate(X)
- anti_patterns: Absence of constraint declarations (:- statements), Only facts without logical rules (pure generate-and-test fallback), Explicit enumeration of all valid configurations instead of constraints, Solver called repeatedly without proper constraint formulation, Post-processing validation of constraints instead of encoding in ASP, Genetic algorithms or evolutionary search used instead of constraint solver, Monte Carlo sampling to find valid solutions, Hard-coded generation logic with manual pathfinding instead of logic rules
- confidence: HIGH
