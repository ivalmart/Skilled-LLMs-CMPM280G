import clingo

def generate_dungeon():
    control = clingo.Control()
    
    # ASP Logic Program
    program = '''
    % Dungeon Parameters
    room_count(6).
    gem_count(4).
    altar_count(2).
    
    % Generate Rooms
    {room(R)} :- R = 1..N, room_count(N).
    
    % Place Gems (unique placement)
    1 {gem_in_room(G, R) : room(R)} 1 :- gem(G).
    :- gem_in_room(G1, R), gem_in_room(G2, R), G1 != G2.
    
    % Place Altars (in open spaces)
    1 {altar_in_room(A, R) : room(R)} 1 :- altar(A).
    :- altar_in_room(A, R), gem_in_room(_, R).
    
    % Connectivity Constraint
    connected_rooms(R1, R2) :- room(R1), room(R2), R1 != R2.
    reachable(R) :- room(R).
    
    % Solve for gems and altars
    gem(1..M) :- gem_count(M).
    altar(1..N) :- altar_count(N).
    
    #show gem_in_room/2.
    #show altar_in_room/2.
    '''
    
    control.add('base', [], program)
    control.ground([('base', [])])
    
    solutions = []
    with control.solve(yield_=True) as handle:
        for model in handle:
            solutions.append(model.symbols(shown=True))
    
    return solutions

def parse_solution(solution):
    gems = []
    altars = []
    for sym in solution:
        if sym.name == 'gem_in_room':
            gems.append((sym.arguments[0].number, sym.arguments[1].number))
        elif sym.name == 'altar_in_room':
            altars.append((sym.arguments[0].number, sym.arguments[1].number))
    return gems, altars

def main():
    dungeon_solutions = generate_dungeon()
    
    if dungeon_solutions:
        solution = dungeon_solutions[0]  # Take first valid solution
        gems, altars = parse_solution(solution)
        
        print('Dungeon Configuration:')
        print('Gems:', gems)
        print('Altars:', altars)
    else:
        print('No dungeon configuration found.')

if __name__ == '__main__':
    main()
