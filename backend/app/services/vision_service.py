from app.services.data_store import get_demo_data


def list_query_images(task_id: str) -> list[dict]:
    data = get_demo_data()
    return [
        image
        for image in data.get("vision_images", [])
        if image.get("task_id") == task_id
    ]


def list_tile_index(task_id: str) -> list[dict]:
    data = get_demo_data()
    return [
        tile
        for tile in data.get("vision_tile_index", [])
        if tile.get("task_id") == task_id
    ]


def get_match_result(task_id: str, image_id: str, top_k: int | None = None) -> dict | None:
    data = get_demo_data()
    for item in data.get("vision_matches", []):
        if item.get("task_id") == task_id and item.get("image_id") == image_id:
            result = _with_ranked_candidates(item)
            total_candidate_count = result["candidate_count"]
            if top_k:
                result["candidates"] = result["candidates"][:top_k]
                result["candidate_count"] = len(result["candidates"])
            result["total_candidate_count"] = total_candidate_count
            return result
    return None


def get_match_by_id(match_id: str) -> dict | None:
    data = get_demo_data()
    for item in data.get("vision_matches", []):
        if item.get("match_id") == match_id:
            return _with_ranked_candidates(item)
    return None


def _with_ranked_candidates(match_result: dict) -> dict:
    result = dict(match_result)
    candidates = sorted(
        [dict(candidate) for candidate in result.get("candidates", [])],
        key=lambda candidate: candidate.get("confidence", 0),
        reverse=True,
    )
    for index, candidate in enumerate(candidates, start=1):
        candidate["rank"] = index
    result["candidates"] = candidates
    result["candidate_count"] = len(candidates)
    result["total_candidate_count"] = len(candidates)
    return result
