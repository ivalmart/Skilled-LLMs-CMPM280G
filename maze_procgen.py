"""
Maze Generator Procgen Prototyping

Implements multiple maze generation algorithms and renders their outputs in HTML for visual comparison.

Usage:
    python maze_procgen.py --size 20 --output mazes.html

Extending:
    - Add new algorithms by subclassing MazeGenerator and implementing generate().
    - Register new algorithms in the ALGORITHMS list.
"""

import random
import argparse
from typing import List, Tuple


# --- Maze Generator Base Class and Registry ---
from abc import ABC, abstractmethod

class MazeGenerator(ABC):
    name = "Base"
    description = "Base maze generator (does nothing)"

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[1 for _ in range(width)] for _ in range(height)]  # 1=wall, 0=path

    @abstractmethod
    def generate(self):
        pass

    def get_grid(self) -> List[List[int]]:
        return self.grid

# --- Verification Hook ---
def verify_maze_algorithm(algo: MazeGenerator) -> bool:
    """
    Verifies that the algorithm does not use generate-and-test anti-patterns.
    Extend this function to check for retry loops or random-walks.
    Returns True if the algorithm is valid, False otherwise.
    """
    # For demo: just check class name (extend with AST/code checks as needed)
    forbidden = ["GenerateAndTest", "RandomWalk"]
    for bad in forbidden:
        if bad.lower() in algo.__class__.__name__.lower():
            return False
    return True

# --- Pipeline Manager ---
class MazeProcgenPipeline:
    """
    Orchestrates maze generation, verification, and rendering for all registered algorithms.
    """
    def __init__(self, algorithms, width, height):
        self.algorithms = algorithms
        self.width = width
        self.height = height
        self.results = []

    def run(self):
        for algo_cls in self.algorithms:
            algo = algo_cls(self.width, self.height)
            algo.generate()
            if not verify_maze_algorithm(algo):
                print(f"[WARN] {algo.name} failed verification and will be skipped.")
                continue
            grid = algo.get_grid()
            svg = maze_to_svg(grid)
            self.results.append((algo.name, algo.description, svg))
        return self.results

# --- How to Extend ---
# To add a new maze algorithm:
# 1. Subclass MazeGenerator and implement generate().
# 2. Register your class in the ALGORITHMS list below.
# 3. Optionally, add a verification rule in verify_maze_algorithm().

# --- DFS Maze Generator ---
class DFSMazeGenerator(MazeGenerator):
    name = "Depth-First Search (DFS)"
    description = "Recursive backtracker maze generation."

    def generate(self):
        w, h = self.width, self.height
        grid = [[1 for _ in range(w)] for _ in range(h)]
        stack = [(1, 1)]
        grid[1][1] = 0
        dirs = [(-2,0),(2,0),(0,-2),(0,2)]
        while stack:
            x, y = stack[-1]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x+dx, y+dy
                if 1 <= nx < w-1 and 1 <= ny < h-1 and grid[ny][nx] == 1:
                    grid[ny][nx] = 0
                    grid[y+dy//2][x+dx//2] = 0
                    stack.append((nx, ny))
                    break
            else:
                stack.pop()
        self.grid = grid

# --- Prim's Maze Generator ---
class PrimsMazeGenerator(MazeGenerator):
    name = "Prim's Algorithm"
    description = "Randomized Prim's algorithm for maze generation."

    def generate(self):
        w, h = self.width, self.height
        grid = [[1 for _ in range(w)] for _ in range(h)]
        walls = []
        x, y = 1, 1
        grid[y][x] = 0
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            nx, ny = x+dx, y+dy
            if 1 <= nx < w-1 and 1 <= ny < h-1:
                walls.append((x+dx, y+dy, x, y))
        while walls:
            wx, wy, px, py = walls.pop(random.randrange(len(walls)))
            if 1 <= wx < w-1 and 1 <= wy < h-1 and grid[wy][wx] == 1:
                grid[wy][wx] = 0
                grid[(wy+py)//2][(wx+px)//2] = 0
                for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
                    nx, ny = wx+dx, wy+dy
                    if 1 <= nx < w-1 and 1 <= ny < h-1 and grid[ny][nx] == 1:
                        walls.append((wx+dx, wy+dy, wx, wy))
        self.grid = grid

# --- Kruskal's Maze Generator ---
class KruskalsMazeGenerator(MazeGenerator):
    name = "Kruskal's Algorithm"
    description = "Randomized Kruskal's algorithm for maze generation."

    def generate(self):
        w, h = self.width, self.height
        grid = [[1 for _ in range(w)] for _ in range(h)]
        sets = dict()
        cells = []
        for y in range(1, h, 2):
            for x in range(1, w, 2):
                grid[y][x] = 0
                sets[(x, y)] = (x, y)
                cells.append((x, y))
        walls = []
        for x, y in cells:
            for dx, dy in [(2,0),(0,2)]:
                nx, ny = x+dx, y+dy
                if nx < w and ny < h:
                    walls.append(((x, y), (nx, ny), (x+dx//2, y+dy//2)))
        random.shuffle(walls)
        def find(cell):
            while sets[cell] != cell:
                cell = sets[cell]
            return cell
        for (x1, y1), (x2, y2), (wx, wy) in walls:
            s1, s2 = find((x1, y1)), find((x2, y2))
            if s1 != s2:
                grid[wy][wx] = 0
                sets[s2] = s1
        self.grid = grid


# --- Algorithm Registry ---
ALGORITHMS = [
    DFSMazeGenerator,
    PrimsMazeGenerator,
    KruskalsMazeGenerator,
    # Add new algorithms here
]

# --- HTML Rendering ---
def maze_to_svg(grid: List[List[int]], cell_size=20) -> str:
    h, w = len(grid), len(grid[0])
    svg = [f'<svg width="{w*cell_size}" height="{h*cell_size}" style="background:#fff">']
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == 1:
                svg.append(f'<rect x="{x*cell_size}" y="{y*cell_size}" width="{cell_size}" height="{cell_size}" fill="#222"/>')
    svg.append('</svg>')
    return '\n'.join(svg)


def render_html(mazes: List[Tuple[str, str, str]], output_file: str):
    html = ["""
    <html><head><title>Maze Generator Comparison</title>
    <style>
    body { font-family: sans-serif; }
    .maze-grid { display: flex; gap: 2em; flex-wrap: wrap; }
    .maze-cell { text-align: center; border: 1px solid #eee; border-radius: 8px; background: #fafafa; padding: 1em; margin-bottom: 1em; box-shadow: 0 2px 8px #0001; }
    .maze-title { font-weight: bold; margin-bottom: 0.2em; }
    .maze-desc { font-size: 0.9em; color: #555; margin-bottom: 0.5em; }
    </style></head><body>
    <h1>Maze Generator Comparison</h1>
    <div class="maze-grid">
    ""]
    for name, desc, svg in mazes:
        html.append(f'<div class="maze-cell"><div class="maze-title">{name}</div><div class="maze-desc">{desc}</div>{svg}</div>')
    html.append("""
    </div>
    <hr><div style='font-size:0.9em;color:#888'>
    <b>Extending:</b> Add new algorithms by subclassing <code>MazeGenerator</code> and registering in <code>ALGORITHMS</code>.<br>
    <b>Verification:</b> Algorithms are checked for anti-patterns before display.<br>
    <b>Source:</b> Inspired by <a href='https://github.com/ivalmart/Skilled-LLMs-CMPM280G/tree/lakitu'>lakitu branch</a> SOM pipeline.
    </div></body></html>
    """)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
    print(f"Wrote {output_file}")

# --- Main Script ---

def main():
    parser = argparse.ArgumentParser(description="Maze Generator Procgen Prototyping (SOM Pipeline)")
    parser.add_argument('--size', type=int, default=21, help='Maze width/height (odd number)')
    parser.add_argument('--output', type=str, default='mazes.html', help='Output HTML file')
    args = parser.parse_args()
    size = args.size | 1  # ensure odd
    pipeline = MazeProcgenPipeline(ALGORITHMS, size, size)
    results = pipeline.run()
    render_html(results, args.output)

if __name__ == '__main__':
    main()
