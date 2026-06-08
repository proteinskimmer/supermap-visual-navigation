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


def get_task(task_id: str) -> dict:
    data = get_demo_data()
    task = data["task"]
    if task["id"] != task_id:
        raise KeyError(f"task not found: {task_id}")
    return task

