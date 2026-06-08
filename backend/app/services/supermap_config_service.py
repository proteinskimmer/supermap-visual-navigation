import copy
import json
from functools import lru_cache
from pathlib import Path

from app.core.config import SUPERMAP_SERVICE_EXAMPLE_PATH, SUPERMAP_SERVICE_LOCAL_PATH


@lru_cache(maxsize=1)
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
    services = []
    for service_id, service in config.get("services", {}).items():
        services.append(
            {
                "id": service_id,
                "name": service.get("name", ""),
                "url": service.get("url", ""),
                "type": service.get("type", service_id),
                "status": service.get("status", "todo"),
            }
        )
    return services


def _select_config_path() -> Path:
    if SUPERMAP_SERVICE_LOCAL_PATH.exists():
        return SUPERMAP_SERVICE_LOCAL_PATH
    return SUPERMAP_SERVICE_EXAMPLE_PATH

