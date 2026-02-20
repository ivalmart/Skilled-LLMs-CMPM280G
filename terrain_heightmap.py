import numpy as np
import noise
import matplotlib.pyplot as plt

def normalize_terrain(terrain):
    return (terrain - terrain.min()) / (terrain.max() - terrain.min())

def generate_terrain(width, height, scale=10.0, octaves=6):
    terrain = np.zeros((width, height))
    for x in range(width):
        for y in range(height):
            terrain[x][y] = noise.pnoise2(x/scale, y/scale, octaves=octaves)
    return normalize_terrain(terrain)

def simulate_rivers(terrain, num_rivers=5):
    rivers = np.zeros_like(terrain)
    for _ in range(num_rivers):
        x, y = np.random.randint(0, terrain.shape[0]), 0
        while y < terrain.shape[1] - 1:
            rivers[x, y] = 1
            neighbors = [
                (x-1, y+1), (x, y+1), (x+1, y+1)
            ]
            valid_neighbors = [
                (nx, ny) for nx, ny in neighbors
                if 0 <= nx < terrain.shape[0] and 0 <= ny < terrain.shape[1]
            ]
            x, y = min(valid_neighbors, key=lambda coord: terrain[coord[0], coord[1]])
    return rivers

def main():
    width, height = 256, 256
    terrain = generate_terrain(width, height)
    rivers = simulate_rivers(terrain)

    plt.figure(figsize=(12, 4))
    plt.subplot(131)
    plt.title('Terrain Heightmap')
    plt.imshow(terrain, cmap='terrain')
    plt.subplot(132)
    plt.title('Rivers')
    plt.imshow(rivers, cmap='Blues')
    plt.subplot(133)
    plt.title('Combined')
    combined = terrain.copy()
    combined[rivers == 1] = 0
    plt.imshow(combined, cmap='terrain')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
