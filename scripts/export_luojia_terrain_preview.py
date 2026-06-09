import csv
import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POINTS_PATH = PROJECT_ROOT / "data_sources/luojia_mountain/raw_test_data/区域地形点.csv"
OUT_PATH = PROJECT_ROOT / "frontend/public/demo/luojia_terrain_preview.json"

GRID_COLS = 72
GRID_ROWS = 40

A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
LON0 = math.radians(114.0)
FALSE_EASTING = 500000.0

# DEM/ortho working extent, EPSG:4547 meters.
WEST = 534169.8512101675
SOUTH = 3379309.826421168
EAST = 535710.0512101675
NORTH = 3380150.0264211684


def inverse_epsg4547(x, y):
    m = y
    mu = m / (A * (1 - E2 / 4 - 3 * E2**2 / 64 - 5 * E2**3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    fp = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )
    sin_fp = math.sin(fp)
    cos_fp = math.cos(fp)
    tan_fp = math.tan(fp)
    c1 = EP2 * cos_fp**2
    t1 = tan_fp**2
    n1 = A / math.sqrt(1 - E2 * sin_fp**2)
    r1 = A * (1 - E2) / ((1 - E2 * sin_fp**2) ** 1.5)
    d = (x - FALSE_EASTING) / n1
    lat = fp - (n1 * tan_fp / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * EP2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * EP2 - 3 * c1**2) * d**6 / 720
    )
    lon = LON0 + (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * EP2 + 24 * t1**2) * d**5 / 120
    ) / cos_fp
    return [math.degrees(lon), math.degrees(lat)]


def cell_index(x, y):
    col = round((x - WEST) / (EAST - WEST) * (GRID_COLS - 1))
    row = round((NORTH - y) / (NORTH - SOUTH) * (GRID_ROWS - 1))
    if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
        return row, col
    return None


def main():
    sums = [[0.0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    counts = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

    with POINTS_PATH.open("r", encoding="utf-8-sig", newline="") as file:
      reader = csv.DictReader(file)
      for record in reader:
          x = float(record["X"])
          y = float(record["Y"])
          z = float(record["Z"])
          index = cell_index(x, y)
          if index is None:
              continue
          row, col = index
          sums[row][col] += z
          counts[row][col] += 1

    heights = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    known = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if counts[row][col]:
                value = sums[row][col] / counts[row][col]
                heights[row][col] = value
                known.append((row, col, value))

    if not known:
        raise RuntimeError("No terrain points fell inside the Luojia extent")

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if heights[row][col] is not None:
                continue
            nearest = min(known, key=lambda item: (item[0] - row) ** 2 + (item[1] - col) ** 2)
            heights[row][col] = nearest[2]

    vertices = []
    z_values = []
    for row in range(GRID_ROWS):
        y = NORTH - (NORTH - SOUTH) * row / (GRID_ROWS - 1)
        for col in range(GRID_COLS):
            x = WEST + (EAST - WEST) * col / (GRID_COLS - 1)
            lon, lat = inverse_epsg4547(x, y)
            z = round(float(heights[row][col]), 2)
            z_values.append(z)
            vertices.append(
                {
                    "lon": round(lon, 9),
                    "lat": round(lat, 9),
                    "height_m": z,
                    "u": round(col / (GRID_COLS - 1), 6),
                    "v": round(row / (GRID_ROWS - 1), 6),
                }
            )

    indices = []
    for row in range(GRID_ROWS - 1):
        for col in range(GRID_COLS - 1):
            a = row * GRID_COLS + col
            b = a + 1
            c = a + GRID_COLS
            d = c + 1
            indices.extend([a, c, b, b, c, d])

    payload = {
        "source": str(POINTS_PATH.relative_to(PROJECT_ROOT)),
        "crs": "EPSG:4547 transformed to WGS84",
        "cols": GRID_COLS,
        "rows": GRID_ROWS,
        "texture": "/demo/luojia_ortho_preview.jpg",
        "z_min": round(min(z_values), 2),
        "z_max": round(max(z_values), 2),
        "vertices": vertices,
        "indices": indices,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({"output": str(OUT_PATH), "vertices": len(vertices), "triangles": len(indices) // 3, "z_min": payload["z_min"], "z_max": payload["z_max"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
