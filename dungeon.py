import random
from collections import deque

def generate():
    grid = [['.' for _ in range(10)] for _ in range(10)]

    for _ in range(25):
        x, y = random.randint(0, 9), random.randint(0, 9)
        if (x, y) not in [(0, 0), (9, 9)]:
            grid[y][x] = '#'

    gem = None
    while not gem:
        x, y = random.randint(0, 9), random.randint(0, 9)
        if grid[y][x] == '.' and (x, y) != (0, 0) and (x, y) != (9, 9):
            gem = (x, y)
            grid[y][x] = 'G'

    altar = None
    while not altar:
        x, y = random.randint(0, 9), random.randint(0, 9)
        if grid[y][x] == '.' and (x, y) != (0, 0) and (x, y) != (9, 9):
            altar = (x, y)
            grid[y][x] = 'A'

    return grid, gem, altar

def pathfind(grid, start, end):
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        (x, y), path = queue.popleft()

        if (x, y) == end:
            return path

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy

            if 0 <= nx < 10 and 0 <= ny < 10:
                if (nx, ny) not in visited and grid[ny][nx] != '#':
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)]))

    return None

def validate(grid, gem, altar):
    path1 = pathfind(grid, (0, 0), gem)
    if not path1:
        return False

    path2 = pathfind(grid, gem, altar)
    if not path2:
        return False

    path3 = pathfind(grid, altar, (9, 9))
    if not path3:
        return False

    return True

def visualize(grid):
    print("\n╔" + "══" * 10 + "╗")
    for row in grid:
        print("║" + "".join(f" {cell}" for cell in row) + " ║")
    print("╚" + "══" * 10 + "╝")
    print("\nLegend: . = floor, # = wall, G = gem, A = altar")
    print("Start: (0,0)  Goal: (9,9)\n")

def main():
    attempts = 0
    while attempts < 100:
        attempts += 1
        grid, gem, altar = generate()

        if validate(grid, gem, altar):
            print(f"✓ Valid dungeon generated (attempt {attempts})")
            visualize(grid)
            return

    print("Failed to generate valid dungeon after 100 attempts")

if __name__ == "__main__":
    main()
