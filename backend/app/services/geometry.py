from math import cos, radians, sqrt


METERS_PER_DEGREE_LAT = 111_320.0


def lonlat_to_xy(point: list[float], origin: list[float]) -> tuple[float, float]:
    lon, lat = point[0], point[1]
    origin_lon, origin_lat = origin[0], origin[1]
    meters_per_degree_lon = METERS_PER_DEGREE_LAT * cos(radians(origin_lat))
    return (
        (lon - origin_lon) * meters_per_degree_lon,
        (lat - origin_lat) * METERS_PER_DEGREE_LAT,
    )


def xy_to_lonlat(x: float, y: float, origin: list[float]) -> list[float]:
    origin_lon, origin_lat = origin[0], origin[1]
    meters_per_degree_lon = METERS_PER_DEGREE_LAT * cos(radians(origin_lat))
    return [
        origin_lon + x / meters_per_degree_lon,
        origin_lat + y / METERS_PER_DEGREE_LAT,
    ]


def distance_m(a: list[float], b: list[float], origin: list[float]) -> float:
    ax, ay = lonlat_to_xy(a, origin)
    bx, by = lonlat_to_xy(b, origin)
    dz = (a[2] if len(a) > 2 else 0.0) - (b[2] if len(b) > 2 else 0.0)
    return sqrt((ax - bx) ** 2 + (ay - by) ** 2 + dz**2)


def point_in_polygon(point: list[float], polygon: list[list[float]]) -> bool:
    x, y = point[0], point[1]
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i][0], polygon[i][1]
        xj, yj = polygon[j][0], polygon[j][1]
        intersects = (yi > y) != (yj > y)
        if intersects:
            x_cross = (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
            if x < x_cross:
                inside = not inside
        j = i
    return inside


def point_to_segment_distance_m(
    point: list[float], start: list[float], end: list[float], origin: list[float]
) -> float:
    px, py = lonlat_to_xy(point, origin)
    ax, ay = lonlat_to_xy(start, origin)
    bx, by = lonlat_to_xy(end, origin)
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return sqrt((px - ax) ** 2 + (py - ay) ** 2)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return sqrt((px - cx) ** 2 + (py - cy) ** 2)


def polyline_distance_m(points: list[list[float]], origin: list[float]) -> float:
    return sum(distance_m(points[index], points[index + 1], origin) for index in range(len(points) - 1))

