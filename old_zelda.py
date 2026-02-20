#!/usr/bin/env python3
"""Zelda-style dungeon generator using Answer Set Programming (ASP).
Uses clingo solver to ensure all gems are reachable and altars are in open spaces."""

import clingo

ASP_PROGRAM = """
% === Domain ===
#const rows=10.
#const cols=12.
cell(X,Y) :- X=1..cols, Y=1..rows.

% === Generate Floor/Wall ===
{ floor(X,Y) } :- cell(X,Y).
wall(X,Y) :- cell(X,Y), not floor(X,Y).

% === Border walls (structural) ===
wall(X,Y) :- cell(X,Y), X=1.
wall(X,Y) :- cell(X,Y), X=cols.
wall(X,Y) :- cell(X,Y), Y=1.
wall(X,Y) :- cell(X,Y), Y=rows.

% === Floor density constraints ===
:- #count{X,Y: floor(X,Y)} < 40.
:- #count{X,Y: floor(X,Y)} > 60.

% === Connectivity - all floors reachable from start ===
start(2,2).
floor(2,2).

reachable(X,Y) :- start(X,Y), floor(X,Y).
reachable(X,Y) :- reachable(X-1,Y), floor(X,Y), X>1.
reachable(X,Y) :- reachable(X+1,Y), floor(X,Y), X<cols.
reachable(X,Y) :- reachable(X,Y-1), floor(X,Y), Y>1.
reachable(X,Y) :- reachable(X,Y+1), floor(X,Y), Y<rows.

:- floor(X,Y), not reachable(X,Y).

% === Gem placement (distribution: 4-8 gems) ===
{ gem(X,Y) } :- floor(X,Y), not start(X,Y).
:- #count{X,Y: gem(X,Y)} < 4.
:- #count{X,Y: gem(X,Y)} > 8.

% === Altar placement - open spaces (5+ adjacent floors) ===
adj_floor_count(X,Y,N) :- floor(X,Y),
    N = #count{X1,Y1: floor(X1,Y1), |X1-X|<=1, |Y1-Y|<=1, (X1,Y1)!=(X,Y)}.

open_space(X,Y) :- floor(X,Y), adj_floor_count(X,Y,N), N >= 5.
{ altar(X,Y) } :- open_space(X,Y).
:- #count{X,Y: altar(X,Y)} != 2.

% === Adjacency constraint - altars not adjacent to gems ===
:- altar(X,Y), gem(X1,Y1), |X-X1|<=1, |Y-Y1|<=1.

% === Structural - no 1x1 isolated floor pockets ===
:- floor(X,Y), not start(X,Y),
   #count{X1,Y1: floor(X1,Y1), |X1-X|+|Y1-Y|=1} < 2.

#show floor/2. #show gem/2. #show altar/2. #show start/2.
"""

def solve_dungeon():
    ctl = clingo.Control(["--rand-freq=0.5"])
    ctl.add("base", [], ASP_PROGRAM)
    ctl.ground([("base", [])])
    result = {}
    def on_model(m):
        result['floor'] = {(s.arguments[0].number, s.arguments[1].number) for s in m.symbols(shown=True) if s.name == 'floor'}
        result['gem'] = {(s.arguments[0].number, s.arguments[1].number) for s in m.symbols(shown=True) if s.name == 'gem'}
        result['altar'] = {(s.arguments[0].number, s.arguments[1].number) for s in m.symbols(shown=True) if s.name == 'altar'}
        result['start'] = next((s.arguments[0].number, s.arguments[1].number) for s in m.symbols(shown=True) if s.name == 'start')
    ctl.solve(on_model=on_model)
    return result if result else None

def render(d):
    if not d: return "No solution!"
    lines = []
    for y in range(1, 11):
        line = ""
        for x in range(1, 13):
            if (x,y) in d['altar']: line += "A"
            elif (x,y) in d['gem']: line += "G"
            elif (x,y) == d['start']: line += "S"
            elif (x,y) in d['floor']: line += "."
            else: line += "#"
        lines.append(line)
    return "\n".join(lines)

def main():
    print("Zelda Dungeon Generator (ASP)\n" + "="*30)
    print("Legend: S=Start  G=Gem  A=Altar  .=Floor  #=Wall\n")
    dungeon = solve_dungeon()
    print(render(dungeon))
    if dungeon:
        print(f"\nStats: {len(dungeon['gem'])} gems (all reachable), {len(dungeon['altar'])} altars (open spaces)")
        print(f"Floor tiles: {len(dungeon['floor'])}, Connected: True")

if __name__ == "__main__":
    main()
