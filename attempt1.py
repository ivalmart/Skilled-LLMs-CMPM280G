#!/usr/bin/env python3
"""Zelda-style dungeon generator using Answer Set Programming (ASP).

Constraints encoded:
- CONNECTIVITY: All rooms reachable from entrance
- PLACEMENT: Gems in rooms, altars in open spaces
- DISTRIBUTION: Items spread out (not adjacent)
- ADJACENCY: Proper neighbor relationships
- STRUCTURAL: Valid room count and layout
"""

import sys

ASP_PROGRAM = """
% Constants
#const w=10.
#const h=10.
#const min_rooms=30.
#const num_gems=5.
#const num_altars=2.

% Grid cells
cell(X,Y) :- X=1..w, Y=1..h.

% Room selection (choice rule - each cell independently)
{ room(X,Y) } :- cell(X,Y).

% STRUCTURAL: minimum room count
:- #count{X,Y: room(X,Y)} < min_rooms.

% Entrance (guaranteed room)
entrance(2,2).
room(2,2).

% Adjacency for connectivity check
adj(X,Y,X+1,Y) :- cell(X,Y), cell(X+1,Y).
adj(X,Y,X,Y+1) :- cell(X,Y), cell(X,Y+1).
adj(X2,Y2,X1,Y1) :- adj(X1,Y1,X2,Y2).

% CONNECTIVITY: transitive closure from entrance
reach(X,Y) :- entrance(X,Y).
reach(X2,Y2) :- reach(X1,Y1), room(X1,Y1), room(X2,Y2), adj(X1,Y1,X2,Y2).

% Constraint: all rooms must be reachable
:- room(X,Y), not reach(X,Y).

% Open space: room with 3+ adjacent rooms
open(X,Y) :- room(X,Y),
    3 <= #count{X2,Y2: room(X2,Y2), adj(X,Y,X2,Y2)}.

% PLACEMENT: gems in any room
{ gem(X,Y) } :- room(X,Y).
:- #count{X,Y: gem(X,Y)} != num_gems.

% PLACEMENT: altars only in open spaces
{ altar(X,Y) } :- open(X,Y).
:- #count{X,Y: altar(X,Y)} != num_altars.

% DISTRIBUTION: gems not adjacent
gem_adj(X1,Y1,X2,Y2) :- gem(X1,Y1), gem(X2,Y2), adj(X1,Y1,X2,Y2).
:- gem_adj(X1,Y1,X2,Y2), X1*100+Y1 < X2*100+Y2.

% DISTRIBUTION: altars not adjacent
:- altar(X1,Y1), altar(X2,Y2), adj(X1,Y1,X2,Y2), X1*100+Y1 < X2*100+Y2.

% ADJACENCY: no overlap between gems and altars
:- gem(X,Y), altar(X,Y).

% Output
#show room/2.
#show gem/2.
#show altar/2.
#show entrance/2.
"""

def solve_dungeon():
    """Execute ASP solver and extract dungeon configuration."""
    try:
        import clingo
    except ImportError:
        print("Error: 'clingo' package required.")
        print("Install with: pip install clingo")
        sys.exit(1)

    solver = clingo.Control(["--stat"])
    solver.add("base", [], ASP_PROGRAM)
    solver.ground([("base", [])])

    dungeon = {"rooms": set(), "gems": set(), "altars": set(), "entrance": None}

    def on_model(model):
        dungeon["rooms"].clear()
        dungeon["gems"].clear()
        dungeon["altars"].clear()
        for sym in model.symbols(shown=True):
            x, y = sym.arguments[0].number, sym.arguments[1].number
            if sym.name == "room":
                dungeon["rooms"].add((x, y))
            elif sym.name == "gem":
                dungeon["gems"].add((x, y))
            elif sym.name == "altar":
                dungeon["altars"].add((x, y))
            elif sym.name == "entrance":
                dungeon["entrance"] = (x, y)

    result = solver.solve(on_model=on_model)
    return dungeon if result.satisfiable else None


def verify_connectivity(dungeon):
    """BFS verification that all rooms are connected."""
    if not dungeon["rooms"]:
        return False
    visited = {dungeon["entrance"]}
    queue = [dungeon["entrance"]]
    while queue:
        x, y = queue.pop(0)
        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            neighbor = (x + dx, y + dy)
            if neighbor in dungeon["rooms"] and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited == dungeon["rooms"]


def count_open_neighbors(dungeon, pos):
    """Count adjacent rooms for open space detection."""
    x, y = pos
    return sum(1 for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]
               if (x+dx, y+dy) in dungeon["rooms"])


def render_dungeon(dungeon):
    """Display dungeon as ASCII visualization."""
    width, height = 10, 10
    print("\n+" + "--" * width + "+")
    for y in range(height, 0, -1):
        row = "|"
        for x in range(1, width + 1):
            pos = (x, y)
            if pos == dungeon["entrance"]:
                row += " E"
            elif pos in dungeon["altars"]:
                row += " A"
            elif pos in dungeon["gems"]:
                row += " G"
            elif pos in dungeon["rooms"]:
                row += " ."
            else:
                row += "##"
        print(row + "|")
    print("+" + "--" * width + "+")


def verify_constraints(dungeon):
    """Verify all constraints are satisfied."""
    print("\nConstraint Verification:")
    print("-" * 30)

    # CONNECTIVITY
    connected = verify_connectivity(dungeon)
    print(f"  CONNECTIVITY:   {'PASS' if connected else 'FAIL'}")

    # PLACEMENT - gems reachable
    gems_reachable = all(g in dungeon["rooms"] for g in dungeon["gems"])
    print(f"  GEMS_REACHABLE: {'PASS' if gems_reachable else 'FAIL'}")

    # PLACEMENT - altars in open spaces
    altars_open = all(count_open_neighbors(dungeon, a) >= 3 for a in dungeon["altars"])
    print(f"  ALTARS_OPEN:    {'PASS' if altars_open else 'FAIL'}")

    # DISTRIBUTION - gems not adjacent
    gem_adj = any(abs(g1[0]-g2[0]) + abs(g1[1]-g2[1]) == 1
                  for g1 in dungeon["gems"] for g2 in dungeon["gems"] if g1 != g2)
    print(f"  GEM_SPREAD:     {'PASS' if not gem_adj else 'FAIL'}")

    # STRUCTURAL
    print(f"  ROOM_COUNT:     {len(dungeon['rooms'])} rooms")
    print(f"  GEM_COUNT:      {len(dungeon['gems'])} gems")
    print(f"  ALTAR_COUNT:    {len(dungeon['altars'])} altars")


def main():
    print("=" * 40)
    print("Zelda Dungeon Generator (ASP-based)")
    print("=" * 40)
    print("\nSolving constraint satisfaction problem...")

    dungeon = solve_dungeon()

    if dungeon:
        render_dungeon(dungeon)
        verify_constraints(dungeon)
        print("\nLegend: E=Entrance  G=Gem  A=Altar  .=Room  ##=Wall")
    else:
        print("\nNo satisfying configuration found!")
        print("Try adjusting constraints.")


if __name__ == "__main__":
    main()
