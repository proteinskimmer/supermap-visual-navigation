import copy
import json
from functools import lru_cache

from app.core.config import DEMO_DATA_PATH


@lru_cache(maxsize=1)
def load_demo_data() -> dict:
    with DEMO_DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_demo_data() -> dict:
    return copy.deepcopy(load_demo_data())


def save_demo_data(data: dict) -> dict:
    DEMO_DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    load_demo_data.cache_clear()
    return get_demo_data()


def get_task(task_id: str) -> dict:
    data = get_demo_data()
    task = data["task"]
    if task["id"] != task_id:
        raise KeyError(f"task not found: {task_id}")
    return task


def get_risk_zones(task_id: str) -> list[dict]:
    data = get_demo_data()
    task = data["task"]
    if task["id"] != task_id:
        raise KeyError(f"task not found: {task_id}")
    return data["risk_zones"]


def replace_risk_zones(task_id: str, risk_zones: list[dict]) -> list[dict]:
    data = get_demo_data()
    task = data["task"]
    if task["id"] != task_id:
        raise KeyError(f"task not found: {task_id}")
    data["risk_zones"] = risk_zones
    return save_demo_data(data)["risk_zones"]


def update_task_endpoints(task_id: str, start: list[float], target: list[float]) -> dict:
    data = get_demo_data()
    task = data["task"]
    if task["id"] != task_id:
        raise KeyError(f"task not found: {task_id}")
    task["start"] = start
    task["target"] = target
    return save_demo_data(data)["task"]
