import argparse
import json
import math
import struct
import zlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data_sources/luojia_mountain/raw_test_data"
DEFAULT_DEMO_JSON = PROJECT_ROOT / "demo_data/task_demo.json"
DEFAULT_INDEX_OUTPUT = PROJECT_ROOT / "demo_data/generated/luojia_vision_tiles.json"
DEFAULT_PREVIEW_DIR = PROJECT_ROOT / "frontend/public/demo/vision_tiles"

TIFF_TYPE_SIZES = {
    1: 1,
    2: 1,
    3: 2,
    4: 4,
    5: 8,
    11: 4,
    12: 8,
}

A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
LON0 = math.radians(114.0)
FALSE_EASTING = 500000.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate visual-navigation tile index from the Luojia orthophoto TIFF."
    )
    parser.add_argument("--demo-json", default=str(DEFAULT_DEMO_JSON), help="Demo JSON to update.")
    parser.add_argument("--image", default="", help="Orthophoto TIFF. Defaults to the first TIFF in raw_test_data.")
    parser.add_argument("--world-file", default="", help="TFW world file. Defaults to the image stem with .tfw.")
    parser.add_argument("--output-index", default=str(DEFAULT_INDEX_OUTPUT), help="Generated tile index JSON output.")
    parser.add_argument("--preview-dir", default=str(DEFAULT_PREVIEW_DIR), help="Directory for generated PNG tile previews.")
    parser.add_argument("--tile-size-px", type=int, default=1024, help="Target source-pixel size of each tile.")
    parser.add_argument("--thumbnail-size", type=int, default=256, help="Max width/height of each PNG preview.")
    parser.add_argument("--task-id", default="task_001", help="Task id written into each tile.")
    parser.add_argument("--update-demo", action="store_true", help="Replace vision_tile_index in the demo JSON.")
    parser.add_argument("--update-matches", action="store_true", help="Rebind precomputed match candidates to generated tiles.")
    parser.add_argument("--no-previews", action="store_true", help="Skip PNG preview generation.")
    return parser.parse_args()


def resolve_path(value):
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def find_orthophoto(source_dir):
    candidates = sorted(source_dir.glob("*.tif"))
    if not candidates:
        raise FileNotFoundError(f"No TIFF files found in {source_dir}")
    return candidates[0]


def read_tiff_tags(path):
    raw = path.read_bytes()
    byte_order = raw[:2]
    if byte_order == b"II":
        endian = "<"
    elif byte_order == b"MM":
        endian = ">"
    else:
        raise ValueError(f"Not a classic TIFF file: {path}")

    magic = struct.unpack_from(endian + "H", raw, 2)[0]
    if magic != 42:
        raise ValueError(f"Unsupported TIFF magic {magic}; only classic TIFF is supported.")

    ifd_offset = struct.unpack_from(endian + "I", raw, 4)[0]
    entry_count = struct.unpack_from(endian + "H", raw, ifd_offset)[0]
    tags = {}
    for index in range(entry_count):
        entry = ifd_offset + 2 + index * 12
        tag, field_type, count = struct.unpack_from(endian + "HHI", raw, entry)
        value_size = TIFF_TYPE_SIZES.get(field_type, 1) * count
        value_offset = entry + 8
        if value_size > 4:
            value_offset = struct.unpack_from(endian + "I", raw, entry + 8)[0]
        tags[tag] = {
            "type": field_type,
            "count": count,
            "offset": value_offset,
            "raw": raw,
            "endian": endian,
        }
    return tags


def tiff_values(tags, tag, default=None):
    item = tags.get(tag)
    if item is None:
        return default
    field_type = item["type"]
    count = item["count"]
    offset = item["offset"]
    raw = item["raw"]
    endian = item["endian"]
    if field_type == 1:
        values = list(raw[offset : offset + count])
    elif field_type == 3:
        values = [struct.unpack_from(endian + "H", raw, offset + i * 2)[0] for i in range(count)]
    elif field_type == 4:
        values = [struct.unpack_from(endian + "I", raw, offset + i * 4)[0] for i in range(count)]
    else:
        return default
    return values[0] if count == 1 else values


class TiledTiffSampler:
    def __init__(self, path):
        self.path = path
        self.raw = path.read_bytes()
        self.tags = read_tiff_tags(path)
        self.width = int(tiff_values(self.tags, 256))
        self.height = int(tiff_values(self.tags, 257))
        self.bits_per_sample = int(tiff_values(self.tags, 258, 8))
        self.compression = int(tiff_values(self.tags, 259, 1))
        self.photometric = int(tiff_values(self.tags, 262, 1))
        self.samples_per_pixel = int(tiff_values(self.tags, 277, 1))
        self.tile_width = int(tiff_values(self.tags, 322, 0))
        self.tile_height = int(tiff_values(self.tags, 323, 0))
        self.tile_offsets = tiff_values(self.tags, 324, [])
        self.tile_byte_counts = tiff_values(self.tags, 325, [])
        if isinstance(self.tile_offsets, int):
            self.tile_offsets = [self.tile_offsets]
        if isinstance(self.tile_byte_counts, int):
            self.tile_byte_counts = [self.tile_byte_counts]
        self.tile_cols = math.ceil(self.width / self.tile_width) if self.tile_width else 0
        self.tile_cache = {}
        self.palette = self._read_palette()
        self.available = (
            self.compression == 1
            and self.bits_per_sample == 8
            and self.samples_per_pixel == 1
            and self.tile_width > 0
            and self.tile_height > 0
            and self.tile_offsets
        )

    def _read_palette(self):
        values = tiff_values(self.tags, 320, [])
        if not values or not isinstance(values, list):
            return None
        colors = len(values) // 3
        palette = []
        for index in range(colors):
            palette.append(
                (
                    values[index] >> 8,
                    values[index + colors] >> 8,
                    values[index + colors * 2] >> 8,
                )
            )
        return palette

    def _tile_data(self, tile_x, tile_y):
        tile_index = tile_y * self.tile_cols + tile_x
        if tile_index in self.tile_cache:
            return self.tile_cache[tile_index]
        if tile_index >= len(self.tile_offsets):
            return b""
        offset = self.tile_offsets[tile_index]
        byte_count = self.tile_byte_counts[tile_index]
        data = self.raw[offset : offset + byte_count]
        self.tile_cache[tile_index] = data
        return data

    def rgb(self, x, y):
        if not self.available:
            return (0, 0, 0)
        x = max(0, min(self.width - 1, int(x)))
        y = max(0, min(self.height - 1, int(y)))
        tile_x = x // self.tile_width
        tile_y = y // self.tile_height
        local_x = x % self.tile_width
        local_y = y % self.tile_height
        data = self._tile_data(tile_x, tile_y)
        offset = local_y * self.tile_width + local_x
        if offset >= len(data):
            return (0, 0, 0)
        value = data[offset]
        if self.palette and value < len(self.palette):
            return self.palette[value]
        return (value, value, value)


def read_world_file(path):
    values = [float(line.strip()) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if len(values) < 6:
        raise ValueError(f"World file must contain six numeric lines: {path}")
    pixel_x, rotate_y, rotate_x, pixel_y, center_x, center_y = values[:6]
    if abs(rotate_x) > 1e-9 or abs(rotate_y) > 1e-9:
        raise ValueError("Rotated world files are not supported by this tile generator.")
    return {
        "pixel_x": pixel_x,
        "pixel_y": pixel_y,
        "west": center_x - pixel_x / 2,
        "north": center_y - pixel_y / 2,
    }


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


def projected_point(world, pixel_x, pixel_y):
    return [
        world["west"] + world["pixel_x"] * pixel_x,
        world["north"] + world["pixel_y"] * pixel_y,
    ]


def bbox_for_window(world, x0, y0, x1, y1):
    sw = projected_point(world, x0, y1)
    se = projected_point(world, x1, y1)
    ne = projected_point(world, x1, y0)
    nw = projected_point(world, x0, y0)
    return [
        rounded_lonlat(inverse_epsg4547(*sw)),
        rounded_lonlat(inverse_epsg4547(*se)),
        rounded_lonlat(inverse_epsg4547(*ne)),
        rounded_lonlat(inverse_epsg4547(*nw)),
    ]


def rounded_lonlat(point):
    return [round(point[0], 9), round(point[1], 9)]


def center_for_bbox(bbox, altitude_m=120.0):
    lon = sum(point[0] for point in bbox) / len(bbox)
    lat = sum(point[1] for point in bbox) / len(bbox)
    return [round(lon, 9), round(lat, 9), altitude_m]


def grid_edges(length, count):
    return [round(index * length / count) for index in range(count + 1)]


def write_png(path, width, height, rows):
    def chunk(kind, data):
        payload = kind + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    raw_rows = b"".join(b"\x00" + row for row in rows)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw_rows, 6))
        + chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def luminance(rgb):
    return int(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])


def thumbnail_and_stats(sampler, window, output_path, max_size, write_preview):
    x0, y0, x1, y1 = window
    source_w = max(1, x1 - x0)
    source_h = max(1, y1 - y0)
    thumb_w = min(max_size, source_w)
    thumb_h = max(1, round(source_h * thumb_w / source_w))
    if thumb_h > max_size:
        thumb_h = max_size
        thumb_w = max(1, round(source_w * thumb_h / source_h))

    rows = []
    lum_rows = []
    for py in range(thumb_h):
        sy = y0 + min(source_h - 1, int((py + 0.5) * source_h / thumb_h))
        row = bytearray()
        lum_row = []
        for px in range(thumb_w):
            sx = x0 + min(source_w - 1, int((px + 0.5) * source_w / thumb_w))
            rgb = sampler.rgb(sx, sy)
            row.extend(rgb)
            lum_row.append(luminance(rgb))
        rows.append(bytes(row))
        lum_rows.append(lum_row)

    if write_preview:
        write_png(output_path, thumb_w, thumb_h, rows)

    values = [value for row in lum_rows for value in row]
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    edge_sum = 0
    edge_count = 0
    for py, row in enumerate(lum_rows):
        for px, value in enumerate(row):
            if px + 1 < thumb_w:
                edge_sum += abs(value - row[px + 1])
                edge_count += 1
            if py + 1 < thumb_h:
                edge_sum += abs(value - lum_rows[py + 1][px])
                edge_count += 1
    edge_mean = edge_sum / max(1, edge_count)
    return {
        "preview_width": thumb_w,
        "preview_height": thumb_h,
        "luminance_mean": round(mean, 2),
        "luminance_variance": round(variance, 2),
        "edge_mean": round(edge_mean, 2),
    }


def estimate_feature_count(world, window, stats):
    x0, y0, x1, y1 = window
    width_m = abs((x1 - x0) * world["pixel_x"])
    height_m = abs((y1 - y0) * world["pixel_y"])
    area_m2 = width_m * height_m
    texture_factor = 0.55 + stats.get("edge_mean", 0) / 45 + stats.get("luminance_variance", 0) / 9000
    texture_factor = max(0.55, min(texture_factor, 1.65))
    return max(80, int(round(area_m2 / 25 * texture_factor)))


def relative_path(path):
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def public_demo_path(path):
    public_root = PROJECT_ROOT / "frontend/public"
    try:
        return "/" + str(path.relative_to(public_root)).replace("\\", "/")
    except ValueError:
        return ""


def generate_tiles(args):
    image_path = resolve_path(args.image) if args.image else find_orthophoto(DEFAULT_SOURCE_DIR)
    world_path = resolve_path(args.world_file) if args.world_file else image_path.with_suffix(".tfw")
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    if not world_path.exists():
        raise FileNotFoundError(world_path)

    sampler = TiledTiffSampler(image_path)
    world = read_world_file(world_path)
    cols = max(1, math.ceil(sampler.width / args.tile_size_px))
    rows = max(1, math.ceil(sampler.height / args.tile_size_px))
    x_edges = grid_edges(sampler.width, cols)
    y_edges = grid_edges(sampler.height, rows)
    preview_dir = resolve_path(args.preview_dir)

    tiles = []
    for row in range(rows):
        for col in range(cols):
            x0, x1 = x_edges[col], x_edges[col + 1]
            y0, y1 = y_edges[row], y_edges[row + 1]
            tile_id = f"luojia_tile_r{row + 1:02d}_c{col + 1:02d}"
            preview_path = preview_dir / f"{tile_id}.png"
            stats = {}
            if sampler.available and not args.no_previews:
                stats = thumbnail_and_stats(
                    sampler,
                    (x0, y0, x1, y1),
                    preview_path,
                    args.thumbnail_size,
                    write_preview=True,
                )
            bbox = bbox_for_window(world, x0, y0, x1, y1)
            tiles.append(
                {
                    "tile_id": tile_id,
                    "task_id": args.task_id,
                    "name": f"Luojia auto tile R{row + 1:02d}C{col + 1:02d}",
                    "center": center_for_bbox(bbox),
                    "bbox": bbox,
                    "source": "luojia_ortho_auto_grid",
                    "feature_count": estimate_feature_count(world, (x0, y0, x1, y1), stats),
                    "tile_image": public_demo_path(preview_path) if sampler.available and not args.no_previews else "",
                    "pixel_bbox": [x0, y0, x1, y1],
                    "grid": {"row": row + 1, "col": col + 1, "rows": rows, "cols": cols},
                    "source_image": relative_path(image_path),
                    "feature_count_method": "sampled_tiff_texture_proxy" if stats else "footprint_area_proxy",
                    "preview_stats": stats,
                }
            )
    return {
        "source_image": relative_path(image_path),
        "world_file": relative_path(world_path),
        "image_width": sampler.width,
        "image_height": sampler.height,
        "tile_size_px": args.tile_size_px,
        "rows": rows,
        "cols": cols,
        "tile_count": len(tiles),
        "crs": "EPSG:4547 transformed to WGS84",
        "tiles": tiles,
    }


def nearest_tile(point, tiles):
    lon, lat = point[0], point[1]
    return min(tiles, key=lambda tile: (tile["center"][0] - lon) ** 2 + (tile["center"][1] - lat) ** 2)


def rebind_matches(demo, tiles):
    for match in demo.get("vision_matches", []):
        for candidate in match.get("candidates", []):
            point = candidate.get("center") or candidate.get("bbox", [[0, 0]])[0]
            tile = nearest_tile(point, tiles)
            altitude = candidate.get("center", [0, 0, tile["center"][2]])[2]
            candidate["tile_id"] = tile["tile_id"]
            candidate["bbox"] = tile["bbox"]
            candidate["center"] = [tile["center"][0], tile["center"][1], altitude]


def main():
    args = parse_args()
    result = generate_tiles(args)
    output_index = resolve_path(args.output_index)
    output_index.parent.mkdir(parents=True, exist_ok=True)
    output_index.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.update_demo:
        demo_path = resolve_path(args.demo_json)
        demo = json.loads(demo_path.read_text(encoding="utf-8"))
        demo["vision_tile_index"] = result["tiles"]
        if args.update_matches:
            rebind_matches(demo, result["tiles"])
        demo_path.write_text(json.dumps(demo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "output_index": str(output_index),
                "tile_count": result["tile_count"],
                "grid": f"{result['rows']}x{result['cols']}",
                "source_image": result["source_image"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
