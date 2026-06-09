from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field


DataT = TypeVar("DataT")
Point3D = list[float]
Point2D = list[float]


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: DataT
    message: str = "ok"


class HealthData(BaseModel):
    status: Literal["ok"]


class AreaGeometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[Point2D]]


class TaskParams(BaseModel):
    min_height_m: float
    max_height_m: float
    safe_distance_m: float
    max_distance_m: float


class TaskSummary(BaseModel):
    id: str
    name: str
    display_name: str
    start: Point3D
    target: Point3D


class Task(TaskSummary):
    area: AreaGeometry
    params: TaskParams


class LayerConfig(BaseModel):
    id: str
    name: str
    type: str
    visible: bool = True
    service_url: str = ""


class RiskZone(BaseModel):
    id: str
    name: str
    type: str
    level: int = Field(ge=1, le=5)
    buffer_m: float
    active: bool = True
    polygon: list[Point2D]


class Obstacle(BaseModel):
    id: str
    name: str
    type: str
    position: Point3D
    height_m: float
    buffer_m: float


class TaskDetailData(BaseModel):
    task: Task
    risk_zones: list[RiskZone]
    obstacles: list[Obstacle]


class Route(BaseModel):
    id: str
    mode: str
    name: str
    points: list[Point3D]
    distance_m: float
    estimated_time_s: int
    turn_count: int = 0
    strategy: str = ""
    score: int = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]


class RiskSegment(BaseModel):
    segment_id: str
    start_index: int = Field(ge=0)
    end_index: int = Field(ge=0)
    risk_type: str
    risk_level: Literal["low", "medium", "high", "critical"] | str
    reason: str
    deduct_score: int = Field(ge=0)


class ElevationSample(BaseModel):
    distance_m: float
    terrain_height_m: float
    flight_height_m: float


class RiskStats(BaseModel):
    distance_m: float
    risk_count: int
    max_deduct_score: int


class RiskAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    segments: list[RiskSegment]
    profile: list[ElevationSample]
    summary: str
    stats: RiskStats


class SimulationEvent(BaseModel):
    time_s: int = Field(ge=0)
    type: str
    title: str
    description: str
    position: Point3D


class SimulationStartData(BaseModel):
    simulation_id: str
    route: Route
    events: list[SimulationEvent]
    state: str


class TemporaryRiskData(BaseModel):
    simulation_id: str
    risk: RiskZone
    affected: bool
    event: SimulationEvent


class ReplanData(BaseModel):
    route: Route
    event: SimulationEvent


class VisionImage(BaseModel):
    id: str
    task_id: str
    name: str
    query_image: str
    capture_time_s: int
    resolution: list[int]
    camera: dict[str, Any]
    scene_tags: list[str]
    expected_center: Point3D


class VisionTile(BaseModel):
    tile_id: str
    task_id: str
    name: str
    center: Point3D
    bbox: list[Point2D]
    source: str
    feature_count: int


class VisionCandidate(BaseModel):
    tile_id: str
    confidence: float = Field(ge=0, le=1)
    matched_points: int = Field(ge=0)
    inlier_ratio: float = Field(ge=0, le=1)
    bbox: list[Point2D]
    center: Point3D
    offset_m: list[float]
    status: str
    reason: str
    rank: int = Field(ge=1)


class VisionMatchResult(BaseModel):
    match_id: str
    task_id: str
    image_id: str
    query_image: str
    provider: str
    status: str
    algorithm_trace: list[str]
    candidates: list[VisionCandidate]
    candidate_count: int
    total_candidate_count: int


class VisionSummary(BaseModel):
    image_count: int
    matched_image_count: int
    best_tile_id: str
    best_confidence: float = Field(ge=0, le=1)
    average_matched_points: float
    geometry_verified: bool
    needs_review_count: int
    summary: str


class SuperMapServiceSummary(BaseModel):
    id: str
    name: str
    url: str
    type: str
    status: str
    runtime_status: str = "not_checked"
    reachable: bool | None = None
    checked_url: str = ""
    http_status: int | None = None
    message: str = ""


class ReportData(BaseModel):
    task: Task
    recommended_route: Route
    risk: RiskAnalysis
    events: list[SimulationEvent]
    vision: VisionMatchResult
    vision_summary: VisionSummary
    summary: str


class RoutePlanRequest(BaseModel):
    task_id: str = "task_001"
    start: Point3D | None = None
    target: Point3D | None = None
    modes: list[str] = Field(default_factory=lambda: ["shortest", "safest", "balanced"])


class RiskAnalyzeRequest(BaseModel):
    task_id: str = "task_001"
    route: Route


class SimulationStartRequest(BaseModel):
    task_id: str = "task_001"
    route: Route


class TemporaryRiskRequest(BaseModel):
    task_id: str = "task_001"
    current_position: Point3D
    time_s: int = 120


class ReplanRequest(BaseModel):
    task_id: str = "task_001"
    current_position: Point3D
    target: Point3D | None = None
    temporary_risks: list[RiskZone] = Field(default_factory=list)
    time_s: int = 120


class VisionMatchRequest(BaseModel):
    task_id: str = "task_001"
    image_id: str = "demo_uav_001"
    top_k: int | None = Field(default=None, ge=1, le=10)
    algorithm_mode: Literal["precomputed"] = "precomputed"
