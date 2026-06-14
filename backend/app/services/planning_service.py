from heapq import heappop, heappush
from math import ceil, sqrt

from app.services.geometry import (
    distance_m,
    lonlat_to_xy,
    point_in_polygon,
    point_to_segment_distance_m,
    polyline_distance_m,
    segment_intersects_polygon,
    segment_to_polygon_distance_m,
    xy_to_lonlat,
)


MODE_WEIGHTS = {
    "shortest": {"risk": 0.2, "smooth": 0.0, "bias": 0.0},
    "safest": {"risk": 10.0, "smooth": 0.4, "bias": 0.35},
    "balanced": {"risk": 4.0, "smooth": 0.25, "bias": 0.18},
}


def plan_routes(task: dict, risk_zones: list[dict], modes: list[str] | None = None, obstacles: list[dict] | None = None) -> list[dict]:
    selected_modes = modes or ["shortest", "safest", "balanced"]
    return [
        _plan_single_route(task, risk_zones, mode, obstacles or [])
        for mode in selected_modes
        if mode in MODE_WEIGHTS
    ]


def replan_route(
    task: dict,
    risk_zones: list[dict],
    current_position: list[float],
    target: list[float],
    obstacles: list[dict] | None = None,
) -> dict:
    patched_task = dict(task)
    patched_task["start"] = current_position
    patched_task["target"] = target
    route = _plan_single_route(patched_task, risk_zones, "balanced", obstacles or [])
    route["id"] = "route_replanned_001"
    route["name"] = "动态重规划航线"
    return route


def _plan_single_route(task: dict, risk_zones: list[dict], mode: str, obstacles: list[dict]) -> dict:
    origin = _area_origin(task["area"])
    grid = _build_grid(task, origin)
    start_cell = _point_to_cell(task["start"], grid, origin)
    target_cell = _point_to_cell(task["target"], grid, origin)
    path = _astar(start_cell, target_cell, grid, task, risk_zones, obstacles, mode, origin)
    route_points = [_cell_to_point(cell, grid, origin, _interpolate_height(task, i, len(path))) for i, cell in enumerate(path)]
    if route_points:
        route_points[0] = _normalize_point(task["start"])
        route_points[-1] = _normalize_point(task["target"])
    route_points = _smooth_visible_route(route_points, risk_zones, obstacles, origin)
    route_points = _simplify_collinear(route_points)
    distance = polyline_distance_m(route_points, origin)
    score = max(35, 96 - int(distance / 1000) * 2 - _route_risk_penalty(route_points, risk_zones, obstacles, origin))
    turn_count = _turn_count(route_points)
    return {
        "id": f"route_{mode}_001",
        "mode": mode,
        "name": {"shortest": "最短航线", "safest": "最安全航线", "balanced": "综合最优航线"}[mode],
        "points": route_points,
        "distance_m": round(distance, 1),
        "estimated_time_s": round(distance / 8.0),
        "turn_count": turn_count,
        "strategy": _strategy_text(mode),
        "score": score,
        "risk_level": _risk_level(score),
    }


def _area_origin(area: dict) -> list[float]:
    ring = area["coordinates"][0]
    return [min(point[0] for point in ring), min(point[1] for point in ring)]


def _build_grid(task: dict, origin: list[float]) -> dict:
    ring = task["area"]["coordinates"][0]
    xy_points = [lonlat_to_xy(point, origin) for point in ring]
    max_x = max(point[0] for point in xy_points)
    max_y = max(point[1] for point in xy_points)
    span = max(max_x, max_y)
    cell_m = max(65.0, min(110.0, span / 16.0))
    return {
        "cell_m": cell_m,
        "cols": max(6, int(ceil(max_x / cell_m)) + 1),
        "rows": max(6, int(ceil(max_y / cell_m)) + 1),
    }


def _point_to_cell(point: list[float], grid: dict, origin: list[float]) -> tuple[int, int]:
    x, y = lonlat_to_xy(point, origin)
    col = max(0, min(grid["cols"] - 1, int(x / grid["cell_m"])))
    row = max(0, min(grid["rows"] - 1, int(y / grid["cell_m"])))
    return col, row


def _cell_to_point(cell: tuple[int, int], grid: dict, origin: list[float], height: float) -> list[float]:
    x = (cell[0] + 0.5) * grid["cell_m"]
    y = (cell[1] + 0.5) * grid["cell_m"]
    lon, lat = xy_to_lonlat(x, y, origin)
    return [round(lon, 6), round(lat, 6), round(height, 1)]


def _normalize_point(point: list[float]) -> list[float]:
    return [round(point[0], 6), round(point[1], 6), round(point[2] if len(point) > 2 else 120.0, 1)]


def _astar(
    start: tuple[int, int],
    target: tuple[int, int],
    grid: dict,
    task: dict,
    risk_zones: list[dict],
    obstacles: list[dict],
    mode: str,
    origin: list[float],
) -> list[tuple[int, int]]:
    frontier = [(0.0, start)]
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    cost_so_far = {start: 0.0}

    while frontier:
        _, current = heappop(frontier)
        if current == target:
            break
        for next_cell in _neighbors(current, grid):
            next_point = _cell_to_point(next_cell, grid, origin, task["start"][2])
            move_cost = _grid_distance(current, next_cell)
            current_point = _cell_to_point(current, grid, origin, task["start"][2])
            if (
                current != start
                and next_cell != target
                and _segment_is_restricted(current_point, next_point, risk_zones, obstacles, origin)
            ):
                continue
            risk_cost = _segment_risk_cost(current_point, next_point, risk_zones, origin)
            bias_cost = _mode_bias_cost(next_cell, grid, mode)
            turn_cost = _turn_cost(current, next_cell, came_from.get(current), mode)
            new_cost = (
                cost_so_far[current]
                + move_cost
                + MODE_WEIGHTS[mode]["risk"] * risk_cost
                + bias_cost
                + turn_cost
            )
            if next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]:
                cost_so_far[next_cell] = new_cost
                priority = new_cost + _grid_distance(next_cell, target)
                heappush(frontier, (priority, next_cell))
                came_from[next_cell] = current

    if target not in came_from:
        return [start, target]

    current = target
    path = []
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path


def _neighbors(cell: tuple[int, int], grid: dict) -> list[tuple[int, int]]:
    result = []
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        candidate = (cell[0] + dx, cell[1] + dy)
        if 0 <= candidate[0] < grid["cols"] and 0 <= candidate[1] < grid["rows"]:
            result.append(candidate)
    return result


def _grid_distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _cell_risk_cost(point: list[float], risk_zones: list[dict], origin: list[float]) -> float:
    cost = 0.0
    for zone in risk_zones:
        if zone.get("active", True) and _point_in_zone_or_buffer(point, zone, origin):
            cost += zone.get("level", 3) * 12
    return cost


def _segment_risk_cost(start: list[float], end: list[float], risk_zones: list[dict], origin: list[float]) -> float:
    cost = 0.0
    for zone in risk_zones:
        if zone.get("active", True) and _segment_hits_zone_or_buffer(start, end, zone, origin):
            cost += zone.get("level", 3) * 100
    samples = 6
    for index in range(samples + 1):
        ratio = index / samples
        point = [
            start[0] + (end[0] - start[0]) * ratio,
            start[1] + (end[1] - start[1]) * ratio,
            start[2] + (end[2] - start[2]) * ratio,
        ]
        cost += _cell_risk_cost(point, risk_zones, origin)
    return cost


def _smooth_visible_route(points: list[list[float]], risk_zones: list[dict], obstacles: list[dict], origin: list[float]) -> list[list[float]]:
    if len(points) <= 2:
        return points
    smoothed = [points[0]]
    index = 0
    while index < len(points) - 1:
        next_index = len(points) - 1
        while next_index > index + 1:
            if _segment_is_clear(points[index], points[next_index], risk_zones, obstacles, origin):
                break
            next_index -= 1
        smoothed.append(points[next_index])
        index = next_index
    return smoothed


def _segment_is_clear(start: list[float], end: list[float], risk_zones: list[dict], obstacles: list[dict], origin: list[float]) -> bool:
    for zone in risk_zones:
        if zone.get("active", True) and _segment_hits_zone_or_buffer(start, end, zone, origin):
            return False
    for obstacle in obstacles:
        if _segment_hits_obstacle_buffer(start, end, obstacle, origin):
            return False
    return True


def _segment_is_restricted(start: list[float], end: list[float], risk_zones: list[dict], obstacles: list[dict], origin: list[float]) -> bool:
    restricted_zone = any(
        zone.get("active", True)
        and _is_hard_restricted_zone(zone)
        and _segment_hits_zone_or_buffer(start, end, zone, origin)
        for zone in risk_zones
    )
    return restricted_zone or any(_segment_hits_obstacle_buffer(start, end, obstacle, origin) for obstacle in obstacles)


def _segment_hits_zone_or_buffer(start: list[float], end: list[float], zone: dict, origin: list[float]) -> bool:
    polygon = zone.get("polygon", [])
    if not polygon:
        return False
    if segment_intersects_polygon(start, end, polygon, origin):
        return True
    buffer_m = float(zone.get("buffer_m", 0) or 0)
    return buffer_m > 0 and segment_to_polygon_distance_m(start, end, polygon, origin) <= buffer_m


def _is_hard_restricted_zone(zone: dict) -> bool:
    return zone.get("type") in {"no_fly", "fire", "landslide"} or zone.get("level", 0) >= 4


def _segment_hits_obstacle_buffer(start: list[float], end: list[float], obstacle: dict, origin: list[float]) -> bool:
    buffer_m = float(obstacle.get("buffer_m", 0) or 0)
    if buffer_m <= 0:
        return False
    return point_to_segment_distance_m(obstacle["position"], start, end, origin) <= buffer_m


def _point_in_zone_or_buffer(point: list[float], zone: dict, origin: list[float]) -> bool:
    polygon = zone.get("polygon", [])
    if not polygon:
        return False
    if point_in_polygon(point, polygon):
        return True
    buffer_m = float(zone.get("buffer_m", 0) or 0)
    if buffer_m <= 0:
        return False
    ring = polygon[:-1] if polygon[0] == polygon[-1] else polygon
    for index, start in enumerate(ring):
        end = ring[(index + 1) % len(ring)]
        if point_to_segment_distance_m(point, start, end, origin) <= buffer_m:
            return True
    return False


def _route_risk_penalty(points: list[list[float]], risk_zones: list[dict], obstacles: list[dict], origin: list[float]) -> int:
    penalty = 0
    for index, point in enumerate(points):
        for zone in risk_zones:
            if _point_in_zone_or_buffer(point, zone, origin):
                penalty += zone.get("level", 3) * 4
            if index < len(points) - 1 and _segment_hits_zone_or_buffer(point, points[index + 1], zone, origin):
                penalty += zone.get("level", 3) * 8
        if index < len(points) - 1:
            for obstacle in obstacles:
                if _segment_hits_obstacle_buffer(point, points[index + 1], obstacle, origin):
                    penalty += 12
    return penalty


def _mode_bias_cost(cell: tuple[int, int], grid: dict, mode: str) -> float:
    if mode == "shortest":
        return 0.0
    center_row = grid["rows"] / 2
    normalized_distance = abs(cell[1] - center_row) / max(center_row, 1)
    if mode == "safest":
        return MODE_WEIGHTS[mode]["bias"] * (1 - normalized_distance)
    return MODE_WEIGHTS[mode]["bias"] * normalized_distance


def _turn_cost(
    current: tuple[int, int],
    next_cell: tuple[int, int],
    previous: tuple[int, int] | None,
    mode: str,
) -> float:
    if previous is None:
        return 0.0
    prev_direction = (current[0] - previous[0], current[1] - previous[1])
    next_direction = (next_cell[0] - current[0], next_cell[1] - current[1])
    return MODE_WEIGHTS[mode]["smooth"] if prev_direction != next_direction else 0.0


def _interpolate_height(task: dict, index: int, total: int) -> float:
    if total <= 1:
        return task["start"][2]
    start_h = task["start"][2]
    target_h = task["target"][2]
    return start_h + (target_h - start_h) * (index / (total - 1))


def _simplify_collinear(points: list[list[float]]) -> list[list[float]]:
    if len(points) <= 2:
        return points
    simplified = [points[0]]
    for index in range(1, len(points) - 1):
        prev = simplified[-1]
        current = points[index]
        nxt = points[index + 1]
        same_lon_direction = round(current[0] - prev[0], 6) == round(nxt[0] - current[0], 6)
        same_lat_direction = round(current[1] - prev[1], 6) == round(nxt[1] - current[1], 6)
        if not (same_lon_direction and same_lat_direction):
            simplified.append(current)
    simplified.append(points[-1])
    return simplified


def _turn_count(points: list[list[float]]) -> int:
    if len(points) < 3:
        return 0
    count = 0
    for index in range(1, len(points) - 1):
        prev = points[index - 1]
        current = points[index]
        nxt = points[index + 1]
        direction_a = (round(current[0] - prev[0], 6), round(current[1] - prev[1], 6))
        direction_b = (round(nxt[0] - current[0], 6), round(nxt[1] - current[1], 6))
        if direction_a != direction_b:
            count += 1
    return count


def _strategy_text(mode: str) -> str:
    return {
        "shortest": "距离优先，允许贴近中低风险区。",
        "safest": "风险避让优先，主动绕开高风险区和障碍缓冲区。",
        "balanced": "综合距离、风险和转弯平滑度，适合作为推荐演示航线。",
    }[mode]


def _risk_level(score: int) -> str:
    if score >= 85:
        return "low"
    if score >= 65:
        return "medium"
    if score >= 40:
        return "high"
    return "critical"
