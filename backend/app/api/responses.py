from typing import Any


def ok(data: Any, message: str = "ok") -> dict[str, Any]:
    return {"success": True, "data": data, "message": message}


def fail(message: str, data: Any = None) -> dict[str, Any]:
    return {"success": False, "data": data, "message": message}
