import argparse
import csv
import json
import math
import struct
from pathlib import Path


TIFF_TYPE_SIZES = {
    1: 1,
    2: 1,
    3: 2,
    4: 4,
    5: 8,
    11: 4,
    12: 8,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build reusable frontend preview scene data from DEM points, orthophoto metadata, and building footprints."
    )
    parser.add_argument("--config", required=True, help="Scene data profile JSON.")
    parser.add_argument("--project-root", default=".", help="Project root used to resolve relative paths.")
    parser.add_argument("--terrain", action="store_true", help="Export terrain preview JSON.")
    parser.add_argument("--buildings", action="store_true", help="Export building preview JSON.")
    parser.add_argument("--manifest", action="store_true", help="Write scene data manifest.")
    parser.add_argument("--all", action="store_true", help="Run all supported exporters.")
    return parser.parse_args()


def resolve_path(project_root, source_dir, value):
    path = Path(value)
    if path.is_absolute():
        return path
    if source_dir and not str(value).startswith(("frontend/", "supermap_file_root/", "docs/", "config/", "scripts/")):
        return project_root / source_dir / path
    return project_root / path


def output_path(project_root, value):
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def relative_or_absolute(project_root, path):
    try:
        return str(path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        return str(path)


def require_file(path, label):
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")


def get_record_value(record, field_name):
    if field_name in record:
        return record[field_name]
    normalized = {key.lower(): value for key, value in record.items()}
    return normalized.get(field_name.lower())


def inverse_transverse_mercator(x, y, projection):
    a = float(projection.get("semi_major_axis", 6378137.0))
    inverse_flattening = float(projection.get("inverse_flattening", 298.257223563))
    f = 1.0 / inverse_flattening
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    lon0 = math.radians(float(projection["central_meridian_deg"]))
    false_easting = float(projection.get("false_easting", 500000.0))
    false_northing = float(projection.get("false_northing", 0.0))

    m = y - false_northing
    mu = m / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
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
    c1 = ep2 * cos_fp**2
    t1 = tan_fp**2
    n1 = a / math.sqrt(1 - e2 * sin_fp**2)
    r1 = a * (1 - e2) / ((1 - e2 * sin_fp**2) ** 1.5)
    d = (x - false_easting) / n1

    lat = fp - (n1 * tan_fp / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720
    )
    lon = lon0 + (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
    ) / cos_fp
    return [math.degrees(lon), math.degrees(lat)]


def make_transform(projection):
    projection_type = projection.get("type", "wgs84").lower()
    if projection_type == "wgs84":
        return lambda x, y: [x, y]
    if projection_type == "transverse_mercator":
        return lambda x, y: inverse_transverse_mercator(x, y, projection)
    raise ValueError(f"Unsupported projection type: {projection_type}")


def read_tiff_dimensions(path):
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
        raise ValueError(f"Unsupported TIFF magic {magic}; only classic TIFF is supported for metadata probing.")

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
        if field_type == 3:
            value = struct.unpack_from(endian + "H", raw, value_offset)[0]
        elif field_type == 4:
            value = struct.unpack_from(endian + "I", raw, value_offset)[0]
        else:
            continue
        tags[tag] = value

    if 256 not in tags or 257 not in tags:
        raise ValueError(f"TIFF width/height tags not found: {path}")
    return tags[256], tags[257]


def read_world_file_extent(world_file, image_file):
    require_file(world_file, "World file")
    require_file(image_file, "Orthophoto")
    values = [float(line.strip()) for line in world_file.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if len(values) < 6:
        raise ValueError(f"World file must contain six numeric lines: {world_file}")

    pixel_x, rotate_y, rotate_x, pixel_y, center_x, center_y = values[:6]
    if abs(rotate_x) > 1e-9 or abs(rotate_y) > 1e-9:
        raise ValueError("Rotated world files are not supported by the lightweight extent reader.")
    width, height = read_tiff_dimensions(image_file)
    west = center_x - pixel_x / 2
    north = center_y - pixel_y / 2
    east = west + pixel_x * width
    south = north + pixel_y * height
    return {
        "west": min(west, east),
        "south": min(south, north),
        "east": max(west, east),
        "north": max(south, north),
    }


def resolve_projected_extent(config, project_root, source_dir):
    extent = config.get("extent", {}).get("projected")
    if extent:
        return {key: float(extent[key]) for key in ("west", "south", "east", "north")}

    orthophoto = config.get("orthophoto", {})
    world_file = orthophoto.get("world_file")
    image_file = orthophoto.get("path")
    if world_file and image_file:
        return read_world_file_extent(
            resolve_path(project_root, source_dir, world_file),
            resolve_path(project_root, source_dir, image_file),
        )
    raise ValueError("Projected extent is required when no orthophoto world file can be used.")


def cell_index(x, y, extent, cols, rows):
    col = round((x - extent["west"]) / (extent["east"] - extent["west"]) * (cols - 1))
    row = round((extent["north"] - y) / (extent["north"] - extent["south"]) * (rows - 1))
    if 0 <= col < cols and 0 <= row < rows:
        return row, col
    return None


def export_terrain(config, project_root):
    source_dir = Path(config.get("source_dir", ""))
    terrain = config["terrain"]
    source = terrain["source"]
    if source.get("type") != "points_csv":
        raise ValueError("Only terrain.source.type=points_csv is supported by the lightweight preview exporter.")

    points_path = resolve_path(project_root, source_dir, source["path"])
    require_file(points_path, "Terrain points CSV")
    extent = resolve_projected_extent(config, project_root, source_dir)
    transform = make_transform(config.get("projection", {"type": "wgs84"}))
    cols = int(terrain.get("grid", {}).get("cols", 72))
    rows = int(terrain.get("grid", {}).get("rows", 40))

    sums = [[0.0 for _ in range(cols)] for _ in range(rows)]
    counts = [[0 for _ in range(cols)] for _ in range(rows)]
    with points_path.open("r", encoding=source.get("encoding", "utf-8-sig"), newline="") as file:
        reader = csv.DictReader(file, delimiter=source.get("delimiter", ","))
        for record in reader:
            x = float(get_record_value(record, source.get("x_field", "X")))
            y = float(get_record_value(record, source.get("y_field", "Y")))
            z = float(get_record_value(record, source.get("z_field", "Z")))
            index = cell_index(x, y, extent, cols, rows)
            if index is None:
                continue
            row, col = index
            sums[row][col] += z
            counts[row][col] += 1

    heights = [[None for _ in range(cols)] for _ in range(rows)]
    known = []
    for row in range(rows):
        for col in range(cols):
            if counts[row][col]:
                value = sums[row][col] / counts[row][col]
                heights[row][col] = value
                known.append((row, col, value))
    if not known:
        raise RuntimeError("No terrain points fell inside the configured extent.")

    for row in range(rows):
        for col in range(cols):
            if heights[row][col] is None:
                nearest = min(known, key=lambda item: (item[0] - row) ** 2 + (item[1] - col) ** 2)
                heights[row][col] = nearest[2]

    vertices = []
    z_values = []
    for row in range(rows):
        y = extent["north"] - (extent["north"] - extent["south"]) * row / (rows - 1)
        for col in range(cols):
            x = extent["west"] + (extent["east"] - extent["west"]) * col / (cols - 1)
            lon, lat = transform(x, y)
            z = round(float(heights[row][col]), 2)
            z_values.append(z)
            vertices.append(
                {
                    "lon": round(lon, 9),
                    "lat": round(lat, 9),
                    "height_m": z,
                    "u": round(col / (cols - 1), 6),
                    "v": round(row / (rows - 1), 6),
                }
            )

    indices = []
    for row in range(rows - 1):
        for col in range(cols - 1):
            a = row * cols + col
            b = a + 1
            c = a + cols
            d = c + 1
            indices.extend([a, c, b, b, c, d])

    output = output_path(project_root, terrain["output"])
    payload = {
        "scene_id": config["scene_id"],
        "source": relative_or_absolute(project_root, points_path),
        "crs": describe_crs(config.get("projection", {})),
        "projected_extent": extent,
        "cols": cols,
        "rows": rows,
        "texture": config.get("orthophoto", {}).get("texture_url"),
        "z_min": round(min(z_values), 2),
        "z_max": round(max(z_values), 2),
        "vertices": vertices,
        "indices": indices,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return {"output": str(output), "vertices": len(vertices), "triangles": len(indices) // 3, "z_min": payload["z_min"], "z_max": payload["z_max"]}


def describe_crs(projection):
    if projection.get("epsg"):
        return f"EPSG:{projection['epsg']} transformed to WGS84"
    return f"{projection.get('type', 'wgs84')} transformed to WGS84"


def read_dbf_records(path, encoding):
    raw = path.read_bytes()
    header_len = struct.unpack_from("<H", raw, 8)[0]
    record_len = struct.unpack_from("<H", raw, 10)[0]
    fields = []
    offset = 32
    field_offset = 1
    while raw[offset] != 0x0D:
        name = raw[offset : offset + 11].split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        length = raw[offset + 16]
        fields.append((name, field_offset, length))
        field_offset += length
        offset += 32

    records = []
    count = struct.unpack_from("<I", raw, 4)[0]
    for index in range(count):
        start = header_len + index * record_len
        if start >= len(raw) or raw[start : start + 1] == b"*":
            continue
        item = {}
        for name, field_start, length in fields:
            value = raw[start + field_start : start + field_start + length].decode(encoding, errors="ignore").strip()
            item[name] = value
        records.append(item)
    return records


def read_polygon_records(path, transform):
    raw = path.read_bytes()
    offset = 100
    polygons = []
    while offset + 8 <= len(raw):
        content_len_words = struct.unpack_from(">i", raw, offset + 4)[0]
        content_start = offset + 8
        content_bytes = content_len_words * 2
        if content_start + 4 > len(raw):
            break
        shape_type = struct.unpack_from("<i", raw, content_start)[0]
        if shape_type in (5, 15, 25):
            num_parts = struct.unpack_from("<i", raw, content_start + 36)[0]
            num_points = struct.unpack_from("<i", raw, content_start + 40)[0]
            parts = list(struct.unpack_from(f"<{num_parts}i", raw, content_start + 44))
            points_start = content_start + 44 + num_parts * 4
            points = [
                struct.unpack_from("<2d", raw, points_start + point_index * 16)
                for point_index in range(num_points)
            ]
            parts.append(num_points)
            rings = []
            for part_index in range(len(parts) - 1):
                ring = [transform(x, y) for x, y in points[parts[part_index] : parts[part_index + 1]]]
                if len(ring) >= 4:
                    rings.append(ring)
            polygons.append(rings)
        elif shape_type == 0:
            polygons.append([])
        offset = content_start + content_bytes
    return polygons


def parse_height(record, height_config):
    field = height_config.get("field")
    if field:
        value = get_record_value(record, field)
        if value not in (None, ""):
            try:
                return clamp_height(float(value), height_config)
            except ValueError:
                pass

    floors_field = height_config.get("floors_field")
    if floors_field:
        value = get_record_value(record, floors_field)
        if value not in (None, ""):
            try:
                return clamp_height(float(value) * float(height_config.get("floor_height_m", 3.0)), height_config)
            except ValueError:
                pass
    return clamp_height(float(height_config.get("default_m", 18.0)), height_config)


def clamp_height(value, height_config):
    return max(float(height_config.get("min_m", 0.0)), min(value, float(height_config.get("max_m", 1000.0))))


def export_buildings(config, project_root):
    source_dir = Path(config.get("source_dir", ""))
    building_config = config["buildings"]
    source = building_config["source"]
    if source.get("type") != "shapefile_polygon":
        raise ValueError("Only buildings.source.type=shapefile_polygon is supported.")

    shp_path = resolve_path(project_root, source_dir, source["path"])
    dbf_path = shp_path.with_suffix(".dbf")
    require_file(shp_path, "Building SHP")
    require_file(dbf_path, "Building DBF")
    transform = make_transform(config.get("projection", {"type": "wgs84"}))
    records = read_dbf_records(dbf_path, source.get("encoding", "utf-8"))
    polygons = read_polygon_records(shp_path, transform)

    id_prefix = building_config.get("id_prefix", f"{config['scene_id']}_building")
    height_config = building_config.get("height", {})
    buildings = []
    for index, rings in enumerate(polygons):
        if not rings:
            continue
        record = records[index] if index < len(records) else {}
        buildings.append(
            {
                "id": f"{id_prefix}_{index + 1:03d}",
                "height_m": round(parse_height(record, height_config), 2),
                "polygon": rings[0],
            }
        )

    output = output_path(project_root, building_config["output"])
    payload = {
        "scene_id": config["scene_id"],
        "source": relative_or_absolute(project_root, shp_path),
        "crs": describe_crs(config.get("projection", {})),
        "height_field": height_config.get("field"),
        "count": len(buildings),
        "buildings": buildings,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output": str(output), "count": len(buildings)}


def write_manifest(config, project_root, results):
    output_value = config.get("outputs", {}).get("manifest")
    if not output_value:
        return None
    output = output_path(project_root, output_value)
    payload = {
        "scene_id": config["scene_id"],
        "display_name": config.get("display_name", config["scene_id"]),
        "projection": config.get("projection", {}),
        "orthophoto": {
            "texture_url": config.get("orthophoto", {}).get("texture_url"),
            "path": config.get("orthophoto", {}).get("path"),
        },
        "exports": results,
        "optional_layers": config.get("optional_layers", []),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output": str(output)}


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / config_path
    config = json.loads(config_path.read_text(encoding="utf-8"))

    run_all = args.all or not (args.terrain or args.buildings or args.manifest)
    results = {}
    if run_all or args.terrain:
        results["terrain"] = export_terrain(config, project_root)
    if run_all or args.buildings:
        results["buildings"] = export_buildings(config, project_root)
    if run_all or args.manifest:
        manifest = write_manifest(config, project_root, results)
        if manifest:
            results["manifest"] = manifest
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
