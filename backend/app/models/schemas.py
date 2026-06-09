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
    source: str = ""
    frame_trigger: str = ""
    route_distance_m: float = 0
    source_tile_id: str = ""
    synthetic_view_note: str = ""


class VisionTile(BaseModel):
    tile_id: str
    task_id: str
    name: str
    center: Point3D
    bbox: list[Point2D]
    source: str
    feature_count: int
    tile_image: str = ""
    pixel_bbox: list[int] = Field(default_factory=list)
    grid: dict[str, int] = Field(default_factory=dict)
    source_image: str = ""
    feature_count_method: str = ""
    preview_stats: dict[str, Any] = Field(default_factory=dict)


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


class NavigationPose(BaseModel):
    lon: float
    lat: float
    altitude_m: float


class CameraPose(NavigationPose):
    yaw_deg: float = 0
    pitch_deg: float = -45
    roll_deg: float = 0


class SyntheticViewCandidate(BaseModel):
    view_id: str
    task_id: str
    image_id: str
    tile_id: str
    image_url: str
    pose: CameraPose
    bbox: list[Point2D]
    terrain_height_m: float
    building_count: int
    render_source: dict[str, Any]
    score_prior: float = Field(ge=0, le=1)
    rank: int = Field(ge=1)


class SyntheticViewRequest(BaseModel):
    task_id: str = "task_001"
    image_id: str
    initial_pose: CameraPose | None = None
    route_prior_pose: CameraPose | None = None
    top_k_tiles: int = Field(default=3, ge=1, le=10)


class SyntheticViewResponse(BaseModel):
    task_id: str
    image_id: str
    query_image: str
    initial_pose: CameraPose
    route_prior_pose: CameraPose
    candidate_count: int
    synthetic_views: list[SyntheticViewCandidate]
    pipeline: list[str]


class SyntheticViewMatch(BaseModel):
    view_id: str
    tile_id: str
    confidence: float = Field(ge=0, le=1)
    matched_points: int = Field(ge=0)
    inlier_ratio: float = Field(ge=0, le=1)
    offset_m: list[float]
    correction_vector_m: list[float]
    error_radius_m: float = Field(ge=0)
    estimated_pose: CameraPose
    status: str
    failure_reason: str = ""
    reason: str = ""
    rank: int = Field(ge=1)


class VisualLocalizationRequest(SyntheticViewRequest):
    matcher_mode: Literal[
        "synthetic_v04",
        "precomputed",
        "precomputed_proxy",
        "opencv_orb",
        "opencv_sift",
        "external_deep_matcher",
    ] = "synthetic_v04"


class VisualLocalizationResult(BaseModel):
    localization_id: str
    task_id: str
    image_id: str
    query_image: str
    provider: str
    status: str
    initial_pose: CameraPose
    route_prior_pose: CameraPose
    best_estimated_pose: CameraPose | None = None
    confidence: float = Field(ge=0, le=1)
    error_radius_m: float = Field(ge=0)
    matched_points: int = Field(ge=0)
    inlier_ratio: float = Field(ge=0, le=1)
    correction_vector_m: list[float]
    synthetic_views: list[SyntheticViewCandidate]
    matches: list[SyntheticViewMatch]
    navigation_effect: str
    failure_reason: str = ""
    pipeline: list[str]


class NavigationVisualPosition(NavigationPose):
    confidence: float = Field(ge=0, le=1)
    tile_id: str = ""
    match_id: str = ""
    image_id: str = ""
    reason: str = ""
    error_radius_m: float = Field(default=0, ge=0)
    correction_vector_m: list[float] = Field(default_factory=list)
    synthetic_view_id: str = ""
    localization_mode: str = ""


class NavigationTelemetry(BaseModel):
    uav_id: str = "UAV-011"
    speed_mps: float = Field(ge=0)
    heading_deg: int = Field(ge=0, le=359)
    pitch_deg: float
    roll_deg: float
    yaw_deg: int = Field(ge=0, le=359)
    battery_pct: int = Field(ge=0, le=100)
    signal: Literal["nominal", "degraded", "review"]
    flight_time: str
    location_source: Literal["reference_route", "visual_fusion", "visual_assisted", "manual_review"]


class NavigationVisualFrame(BaseModel):
    image_id: str
    name: str
    query_image: str
    capture_time_s: int = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    matched_points: int = Field(ge=0)
    inlier_ratio: float = Field(ge=0, le=1)
    tile_id: str = ""
    status: str
    reason: str
    synthetic_view_id: str = ""
    synthetic_image: str = ""
    error_radius_m: float = Field(default=0, ge=0)
    correction_vector_m: list[float] = Field(default_factory=list)


class NavigationEvent(BaseModel):
    time_s: int = Field(ge=0)
    type: str
    title: str
    description: str
    position: Point3D


class NavigationStateFrame(BaseModel):
    session_id: str
    time_s: int = Field(ge=0)
    reference_position: NavigationPose
    visual_position: NavigationVisualPosition | None = None
    fused_position: NavigationPose
    deviation_m: float = Field(ge=0)
    navigation_mode: Literal["autonomous", "assisted", "review"]
    telemetry: NavigationTelemetry
    visual_frame: NavigationVisualFrame | None = None
    active_frame_id: str = ""
    active_route_id: str
    active_event: NavigationEvent | None = None
    events: list[NavigationEvent] = Field(default_factory=list)


class NavigationSession(BaseModel):
    session_id: str
    task_id: str
    active_route_id: str
    route: Route
    duration_s: int = Field(ge=1)
    state: Literal["ready"]
    timeline: list[NavigationStateFrame]
    events: list[NavigationEvent]


class NavigationStartRequest(BaseModel):
    task_id: str = "task_001"
    route: Route
    mode: Literal["autonomous", "assisted"] = "autonomous"


class NavigationLocalizeRequest(BaseModel):
    task_id: str = "task_001"
    image_id: str
    route: Route | None = None


class NavigationReplanRequest(BaseModel):
    session_id: str
    time_s: int = Field(ge=0)
    temporary_risks: list[RiskZone] = Field(default_factory=list)


class RoutePlanRequest(BaseModel):
    task_id: str = "task_001"
    start: Point3D | None = None
    target: Point3D | None = None
    modes: list[str] = Field(default_factory=lambda: ["shortest", "safest", "balanced"])


class RiskAnalyzeRequest(BaseModel):
    task_id: str = "task_001"
    route: Route


class RiskZonesUpdateRequest(BaseModel):
    risk_zones: list[RiskZone]


class RiskZonesUpdateData(BaseModel):
    task_id: str
    risk_zones: list[RiskZone]
    count: int = Field(ge=0)


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
