import copy
import json
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.core.config import SUPERMAP_SERVICE_EXAMPLE_PATH, SUPERMAP_SERVICE_LOCAL_PATH

HTTP_TIMEOUT_SECONDS = 3


def load_supermap_config() -> dict:
    config_path = _select_config_path()
    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)
    config["_meta"] = {
        "source": str(config_path),
        "using_local_config": config_path == SUPERMAP_SERVICE_LOCAL_PATH,
    }
    return config


def get_supermap_config() -> dict:
    return copy.deepcopy(load_supermap_config())


def list_supermap_services() -> list[dict]:
    config = get_supermap_config()
    runtime = get_supermap_status(config)
    runtime_services = runtime.get("services", {})
    services = []
    for service_id, service in config.get("services", {}).items():
        runtime_service = runtime_services.get(service_id, {})
        services.append(
            {
                "id": service_id,
                "name": service.get("name", ""),
                "url": service.get("url", ""),
                "type": service.get("type", service_id),
                "status": service.get("status", "todo"),
                "runtime_status": runtime_service.get("runtime_status", "not_checked"),
                "reachable": runtime_service.get("reachable"),
                "checked_url": runtime_service.get("checked_url", ""),
                "http_status": runtime_service.get("http_status"),
                "message": runtime_service.get("message", ""),
            }
        )
    return services


def get_supermap_status(config: dict | None = None) -> dict:
    config = copy.deepcopy(config or get_supermap_config())
    services = config.get("services", {})
    layers = config.get("layers", {})

    scene_status = _check_json_url(
        _json_url(services.get("scene", {}).get("url", ""), "scenes"),
        "scene list",
    )
    map_status = _check_map_service(services.get("map", {}))
    data_status = _check_data_service(services.get("data", {}), layers)

    service_statuses = {
        "scene": scene_status,
        "map": map_status["service"],
        "data": data_status["service"],
    }
    layer_statuses = _build_layer_statuses(layers, data_status.get("dataset_names", []))

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "iserver": config.get("iserver", {}),
        "services": service_statuses,
        "map": {
            "name": map_status.get("map_name", ""),
            "accessible": map_status["service"].get("reachable", False),
            "epsg": map_status.get("epsg"),
            "bounds": map_status.get("bounds"),
            "layer_count": map_status.get("layer_count", 0),
            "datasets": map_status.get("dataset_names", []),
        },
        "data": {
            "accessible": data_status["service"].get("reachable", False),
            "datasource": data_status.get("datasource", ""),
            "dataset_count": data_status.get("dataset_count", 0),
            "dataset_names": data_status.get("dataset_names", []),
        },
        "layers": layer_statuses,
        "all_expected_layers_accessible": all(layer["accessible"] for layer in layer_statuses),
    }


def _select_config_path() -> Path:
    if SUPERMAP_SERVICE_LOCAL_PATH.exists():
        return SUPERMAP_SERVICE_LOCAL_PATH
    return SUPERMAP_SERVICE_EXAMPLE_PATH


def _json_url(base_url: str, resource: str = "") -> str:
    if not base_url:
        return ""
    stripped = base_url.rstrip("/")
    if stripped.endswith(".json"):
        return stripped
    if resource:
        return f"{stripped}/{resource}.json"
    return f"{stripped}.json"


def _check_json_url(url: str, label: str) -> dict:
    if not url:
        return {
            "runtime_status": "missing_url",
            "reachable": False,
            "checked_url": "",
            "http_status": None,
            "message": f"{label} url is not configured",
        }

    try:
        request = Request(url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            content = response.read().decode("utf-8-sig")
            payload = json.loads(content) if content else None
            return {
                "runtime_status": "verified",
                "reachable": True,
                "checked_url": url,
                "http_status": response.status,
                "message": "ok",
                "payload": payload,
            }
    except HTTPError as exc:
        return {
            "runtime_status": "http_error",
            "reachable": False,
            "checked_url": url,
            "http_status": exc.code,
            "message": str(exc),
        }
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {
            "runtime_status": "unreachable",
            "reachable": False,
            "checked_url": url,
            "http_status": None,
            "message": str(exc),
        }


def _check_map_service(service: dict) -> dict:
    resource_url = service.get("resource_url", "")
    map_name = resource_url.rstrip("/").split("/")[-1] if resource_url else ""
    if not resource_url:
        base_url = service.get("url", "")
        map_name = "low_altitude_demo_map"
        resource_url = f"{base_url.rstrip('/')}/{quote(map_name)}" if base_url else ""

    metadata = _check_json_url(_json_url(resource_url), "map metadata")
    layers = _check_json_url(f"{resource_url.rstrip('/')}/layers.json" if resource_url else "", "map layers")
    payload = metadata.get("payload") or {}
    layers_payload = layers.get("payload") or []

    dataset_names = []
    try:
        dataset_names = [
            layer.get("datasetInfo", {}).get("name")
            for layer in layers_payload[0].get("subLayers", {}).get("layers", [])
            if layer.get("datasetInfo", {}).get("name")
        ]
    except (IndexError, AttributeError):
        dataset_names = []

    service_status = metadata.copy()
    service_status.pop("payload", None)
    if metadata.get("reachable") and not layers.get("reachable"):
        service_status["runtime_status"] = "partial"
        service_status["reachable"] = False
        service_status["message"] = f"metadata ok, layers failed: {layers.get('message', '')}"

    return {
        "service": service_status,
        "map_name": map_name,
        "epsg": payload.get("prjCoordSys", {}).get("epsgCode"),
        "bounds": payload.get("bounds"),
        "layer_count": len(dataset_names),
        "dataset_names": dataset_names,
    }


def _check_data_service(service: dict, layers: dict) -> dict:
    base_url = service.get("url", "").rstrip("/")
    datasources = _check_json_url(f"{base_url}/datasources.json" if base_url else "", "data datasources")
    datasource_payload = datasources.get("payload") or {}
    datasource_names = datasource_payload.get("datasourceNames") or []
    datasource = datasource_names[0] if datasource_names else service.get("datasource", "low_altitude_demo")
    url = f"{base_url}/datasources/{quote(datasource)}/datasets.json" if base_url else ""
    datasets = _check_json_url(url, "data datasets")
    payload = datasets.get("payload") or {}
    dataset_names = payload.get("datasetNames") or []

    service_status = datasets.copy()
    service_status.pop("payload", None)
    if not datasources.get("reachable") and datasets.get("reachable"):
        service_status["runtime_status"] = "partial"
        service_status["reachable"] = False
        service_status["message"] = f"datasets ok, datasources failed: {datasources.get('message', '')}"
    expected = [layer.get("dataset") for layer in layers.values() if layer.get("dataset")]
    missing = sorted(set(expected) - set(dataset_names))
    if datasets.get("reachable") and missing:
        service_status["runtime_status"] = "partial"
        service_status["reachable"] = False
        service_status["message"] = "missing datasets: " + ", ".join(missing)

    return {
        "service": service_status,
        "datasource": datasource,
        "dataset_count": payload.get("datasetCount", len(dataset_names)),
        "dataset_names": dataset_names,
    }


def _build_layer_statuses(layers: dict, dataset_names: list[str]) -> list[dict]:
    available = set(dataset_names)
    result = []
    for layer_id, layer in layers.items():
        dataset = layer.get("dataset", "")
        accessible = dataset in available
        result.append(
            {
                "id": layer_id,
                "dataset": dataset,
                "geometry": layer.get("geometry", ""),
                "service": layer.get("service", "data"),
                "accessible": accessible,
                "runtime_status": "verified" if accessible else "missing",
            }
        )
    return result
