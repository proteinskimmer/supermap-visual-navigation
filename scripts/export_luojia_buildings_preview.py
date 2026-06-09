import json
import math
import struct
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHP_PATH = PROJECT_ROOT / "data_sources/luojia_mountain/raw_student_output/珞珈山周边建筑3D.shp"
DBF_PATH = SHP_PATH.with_suffix(".dbf")
OUT_PATH = PROJECT_ROOT / "frontend/public/demo/luojia_buildings_preview.json"

A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
LON0 = math.radians(114.0)
FALSE_EASTING = 500000.0


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


def read_dbf_records(path):
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
            value = raw[start + field_start : start + field_start + length].decode("utf-8", errors="ignore").strip()
            item[name] = value
        records.append(item)
    return records


def read_polygon_records(path):
    raw = path.read_bytes()
    offset = 100
    polygons = []
    while offset + 8 <= len(raw):
        content_len_words = struct.unpack_from(">i", raw, offset + 4)[0]
        content_start = offset + 8
        content_bytes = content_len_words * 2
        shape_type = struct.unpack_from("<i", raw, content_start)[0]
        if shape_type == 5:
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
                ring = [inverse_epsg4547(x, y) for x, y in points[parts[part_index] : parts[part_index + 1]]]
                if len(ring) >= 4:
                    rings.append(ring)
            polygons.append(rings)
        offset = content_start + content_bytes
    return polygons


def parse_height(record):
    for key in ("HEIGHT_M", "Height_M", "height_m"):
        value = record.get(key)
        if value:
            try:
                return max(6.0, min(float(value), 90.0))
            except ValueError:
                pass
    return 18.0


def main():
    records = read_dbf_records(DBF_PATH)
    polygons = read_polygon_records(SHP_PATH)
    buildings = []
    for index, rings in enumerate(polygons):
        if not rings:
            continue
        height = parse_height(records[index] if index < len(records) else {})
        ring = rings[0]
        buildings.append(
            {
                "id": f"luojia_building_{index + 1:03d}",
                "height_m": round(height, 2),
                "polygon": ring,
            }
        )

    payload = {
        "source": str(SHP_PATH.relative_to(PROJECT_ROOT)),
        "crs": "EPSG:4547 transformed to WGS84",
        "height_field": "HEIGHT_M",
        "count": len(buildings),
        "buildings": buildings,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT_PATH), "count": len(buildings)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
