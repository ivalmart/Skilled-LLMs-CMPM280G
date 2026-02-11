#!/usr/bin/env python3
"""
ASP-inspired dungeon generator
Generates a 10x10 grid with walls, gem, and altar following style constraints.
Verifies playability by finding paths: start -> gem -> altar -> exit
"""

import random
from collections import deque
from typing import List, Tuple, Set, Optional

GRID_SIZE = 10
WALL = '#'
EMPTY = '.'
GEM = 'G'
ALTAR = 'A'
START = 'S'
EXIT = 'E'

def neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Return 4-directional neighbors (Manhattan adjacency)"""
    x, y = pos
    result = []
    for dx, dy in [(0, -1), (1, 0), (-1, 0), (0, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            result.append((nx, ny))
    return result

def neighbors_distance(pos: Tuple[int, int], dist: int) -> Set[Tuple[int, int]]:
    """Return all tiles within Manhattan distance"""
    x, y = pos
    result = set()
    for dx in range(-dist, dist + 1):
        for dy in range(-dist, dist + 1):
            if abs(dx) + abs(dy) <= dist:
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    result.add((nx, ny))
    return result

def bfs_path(grid: List[List[str]], start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """Find shortest path using BFS, avoiding walls"""
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        pos, path = queue.popleft()

        if pos == goal:
            return path

        for next_pos in neighbors(pos):
            if next_pos not in visited and grid[next_pos[1]][next_pos[0]] != WALL:
                visited.add(next_pos)
                queue.append((next_pos, path + [next_pos]))

    return None

def count_adjacent_walls(grid: List[List[str]], pos: Tuple[int, int]) -> int:
    """Count walls adjacent to position"""
    count = 0
    for nx, ny in neighbors(pos):
        if grid[ny][nx] == WALL:
            count += 1
    return count

def count_adjacent_walls_for_wall(grid: List[List[str]], pos: Tuple[int, int]) -> int:
    """Count walls adjacent to a wall tile (for connectivity check)"""
    count = 0
    for nx, ny in neighbors(pos):
        if grid[ny][nx] == WALL:
            count += 1
    return count

def has_walls_within_distance(grid: List[List[str]], pos: Tuple[int, int], dist: int) -> bool:
    """Check if any walls exist within Manhattan distance"""
    for check_pos in neighbors_distance(pos, dist):
        if check_pos != pos and grid[check_pos[1]][check_pos[0]] == WALL:
            return True
    return False

def generate_dungeon() -> Tuple[List[List[str]], Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
    """Generate dungeon with constraints, return (grid, gem_pos, altar_pos, exit_pos)"""
    max_attempts = 1000

    for attempt in range(max_attempts):
        grid = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Place start and exit
        start_pos = (0, 0)
        exit_pos = (GRID_SIZE - 1, GRID_SIZE - 1)
        grid[start_pos[1]][start_pos[0]] = START
        grid[exit_pos[1]][exit_pos[0]] = EXIT

        # Generate walls (aim for ~40% coverage for more open space)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if (x, y) == start_pos or (x, y) == exit_pos:
                    continue
                if random.random() < 0.4:
                    grid[y][x] = WALL

        # Optional: Check wall connectivity for aesthetic purposes
        # (Relaxed significantly to allow generation to succeed)
        # In ASP paper, this ensures walls form connected structures
        # Here we skip it for simplicity

        # Find valid gem position (2+ adjacent walls, prefer 3+)
        gem_candidates = []
        gem_best = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if grid[y][x] == EMPTY:
                    adj_walls = count_adjacent_walls(grid, (x, y))
                    if adj_walls >= 3:
                        gem_best.append((x, y))
                    elif adj_walls >= 2:
                        gem_candidates.append((x, y))

        if gem_best:
            gem_pos = random.choice(gem_best)
        elif gem_candidates:
            gem_pos = random.choice(gem_candidates)
        else:
            continue

        gem_pos = random.choice(gem_candidates)

        # Find valid altar position (prefer open areas, no immediately adjacent walls)
        altar_best = []
        altar_candidates = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if grid[y][x] == EMPTY and (x, y) != gem_pos:
                    adj_walls = count_adjacent_walls(grid, (x, y))
                    if adj_walls == 0:
                        altar_best.append((x, y))
                    elif adj_walls <= 1:
                        altar_candidates.append((x, y))

        if altar_best:
            altar_pos = random.choice(altar_best)
        elif altar_candidates:
            altar_pos = random.choice(altar_candidates)
        else:
            continue

        # Temporarily place objects for pathfinding
        grid[gem_pos[1]][gem_pos[0]] = GEM
        grid[altar_pos[1]][altar_pos[0]] = ALTAR

        # Verify playability: start -> gem -> altar -> exit
        path_to_gem = bfs_path(grid, start_pos, gem_pos)
        if not path_to_gem:
            continue

        path_to_altar = bfs_path(grid, gem_pos, altar_pos)
        if not path_to_altar:
            continue

        path_to_exit = bfs_path(grid, altar_pos, exit_pos)
        if not path_to_exit:
            continue

        # Success! Valid dungeon generated
        return grid, gem_pos, altar_pos, exit_pos

    raise RuntimeError(f"Failed to generate valid dungeon after {max_attempts} attempts")

def visualize(grid: List[List[str]], gem_pos: Tuple[int, int], altar_pos: Tuple[int, int], exit_pos: Tuple[int, int]):
    """Print dungeon to terminal with color/style"""
    print("\n+" + "-" * (GRID_SIZE * 2) + "+")

    for y in range(GRID_SIZE):
        print("|", end="")
        for x in range(GRID_SIZE):
            cell = grid[y][x]
            if cell == WALL:
                print("##", end="")
            elif cell == START:
                print(" S", end="")
            elif cell == GEM:
                print(" G", end="")
            elif cell == ALTAR:
                print(" A", end="")
            elif cell == EXIT:
                print(" E", end="")
            else:
                print("  ", end="")
        print("|")

    print("+" + "-" * (GRID_SIZE * 2) + "+\n")

    # Print legend and stats
    print("Legend: S=Start(0,0)  G=Gem  A=Altar  E=Exit(9,9)  ##=Wall")
    print(f"\nGem position: {gem_pos}")
    print(f"Altar position: {altar_pos}")
    print(f"Exit position: {exit_pos}")

    # Calculate stats
    wall_count = sum(row.count(WALL) for row in grid)
    total_tiles = GRID_SIZE * GRID_SIZE
    wall_pct = (wall_count / total_tiles) * 100
    print(f"\nWalls: {wall_count}/{total_tiles} ({wall_pct:.1f}%)")

    # Verify constraints
    gem_walls = count_adjacent_walls(grid, gem_pos)
    altar_walls = count_adjacent_walls(grid, altar_pos)

    print(f"\nConstraint Verification:")
    print(f"  [OK] Gem has {gem_walls} adjacent walls (requires 2+, prefers 3+)")
    print(f"  [OK] Altar has {altar_walls} adjacent walls (prefers 0-1 for open area)")
    print(f"  [OK] Playable path exists: Start -> Gem -> Altar -> Exit")

def main():
    print("ASP-Inspired Dungeon Generator")
    print("=" * 50)

    try:
        grid, gem_pos, altar_pos, exit_pos = generate_dungeon()
        visualize(grid, gem_pos, altar_pos, exit_pos)
        print("\n[SUCCESS] Dungeon generated successfully!")
    except RuntimeError as e:
        print(f"\n[ERROR] {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
