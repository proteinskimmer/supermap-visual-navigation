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


def segment_to_segment_distance_m(
    start_a: list[float],
    end_a: list[float],
    start_b: list[float],
    end_b: list[float],
    origin: list[float],
) -> float:
    ax, ay = lonlat_to_xy(start_a, origin)
    bx, by = lonlat_to_xy(end_a, origin)
    cx, cy = lonlat_to_xy(start_b, origin)
    dx, dy = lonlat_to_xy(end_b, origin)
    if _segments_intersect_xy((ax, ay), (bx, by), (cx, cy), (dx, dy)):
        return 0.0
    return min(
        _point_to_segment_distance_xy((ax, ay), (cx, cy), (dx, dy)),
        _point_to_segment_distance_xy((bx, by), (cx, cy), (dx, dy)),
        _point_to_segment_distance_xy((cx, cy), (ax, ay), (bx, by)),
        _point_to_segment_distance_xy((dx, dy), (ax, ay), (bx, by)),
    )


def segment_intersects_polygon(start: list[float], end: list[float], polygon: list[list[float]], origin: list[float]) -> bool:
    if not polygon:
        return False
    if point_in_polygon(start, polygon) or point_in_polygon(end, polygon):
        return True
    ring = polygon[:-1] if polygon[0] == polygon[-1] else polygon
    for index, edge_start in enumerate(ring):
        edge_end = ring[(index + 1) % len(ring)]
        if segment_to_segment_distance_m(start, end, edge_start, edge_end, origin) <= 1e-6:
            return True
    return False


def segment_to_polygon_distance_m(start: list[float], end: list[float], polygon: list[list[float]], origin: list[float]) -> float:
    if not polygon:
        return float("inf")
    if segment_intersects_polygon(start, end, polygon, origin):
        return 0.0
    ring = polygon[:-1] if polygon[0] == polygon[-1] else polygon
    return min(
        segment_to_segment_distance_m(start, end, edge_start, ring[(index + 1) % len(ring)], origin)
        for index, edge_start in enumerate(ring)
    )


def polyline_distance_m(points: list[list[float]], origin: list[float]) -> float:
    return sum(distance_m(points[index], points[index + 1], origin) for index in range(len(points) - 1))


def _point_to_segment_distance_xy(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return sqrt((px - ax) ** 2 + (py - ay) ** 2)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return sqrt((px - cx) ** 2 + (py - cy) ** 2)


def _segments_intersect_xy(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    def orientation(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> float:
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    def on_segment(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> bool:
        eps = 1e-9
        return (
            min(p[0], r[0]) - eps <= q[0] <= max(p[0], r[0]) + eps
            and min(p[1], r[1]) - eps <= q[1] <= max(p[1], r[1]) + eps
        )

    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)
    eps = 1e-9
    if o1 * o2 < -eps and o3 * o4 < -eps:
        return True
    if abs(o1) <= eps and on_segment(a, c, b):
        return True
    if abs(o2) <= eps and on_segment(a, d, b):
        return True
    if abs(o3) <= eps and on_segment(c, a, d):
        return True
    if abs(o4) <= eps and on_segment(c, b, d):
        return True
    return False
