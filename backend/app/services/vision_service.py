from typing import Protocol

from app.services.data_store import get_demo_data


class VisionProvider(Protocol):
    provider_id: str

    def list_query_images(self, task_id: str) -> list[dict]:
        ...

    def list_tile_index(self, task_id: str) -> list[dict]:
        ...

    def get_match_result(self, task_id: str, image_id: str, top_k: int | None = None) -> dict | None:
        ...

    def get_match_by_id(self, match_id: str) -> dict | None:
        ...


class PrecomputedVisionProvider:
    provider_id = "precomputed_demo"

    def list_query_images(self, task_id: str) -> list[dict]:
        data = get_demo_data()
        return [
            image
            for image in data.get("vision_images", [])
            if image.get("task_id") == task_id
        ]

    def list_tile_index(self, task_id: str) -> list[dict]:
        data = get_demo_data()
        return [
            tile
            for tile in data.get("vision_tile_index", [])
            if tile.get("task_id") == task_id
        ]

    def get_match_result(self, task_id: str, image_id: str, top_k: int | None = None) -> dict | None:
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

    def get_match_by_id(self, match_id: str) -> dict | None:
        data = get_demo_data()
        for item in data.get("vision_matches", []):
            if item.get("match_id") == match_id:
                return _with_ranked_candidates(item)
        return None


class DinoRetrieverProvider:
    provider_id = "dinov2_retriever"


class LocalFeatureProvider:
    provider_id = "local_feature_matcher"


class RansacVerifier:
    provider_id = "ransac_verifier"


_provider: VisionProvider = PrecomputedVisionProvider()


def list_query_images(task_id: str) -> list[dict]:
    return _provider.list_query_images(task_id)


def list_tile_index(task_id: str) -> list[dict]:
    return _provider.list_tile_index(task_id)


def get_match_result(task_id: str, image_id: str, top_k: int | None = None) -> dict | None:
    return _provider.get_match_result(task_id, image_id, top_k)


def get_match_by_id(match_id: str) -> dict | None:
    return _provider.get_match_by_id(match_id)


def list_match_results(task_id: str, top_k: int | None = None) -> list[dict]:
    images = list_query_images(task_id)
    results = []
    for image in images:
        result = get_match_result(task_id, image["id"], top_k)
        if result:
            results.append(result)
    return results


def build_vision_summary(task_id: str) -> dict:
    results = list_match_results(task_id)
    best_candidates = [
        _best_candidate(result)
        for result in results
        if _best_candidate(result)
    ]
    if not results or not best_candidates:
        return {
            "image_count": 0,
            "matched_image_count": 0,
            "best_tile_id": "",
            "best_confidence": 0,
            "average_matched_points": 0,
            "geometry_verified": False,
            "needs_review_count": 0,
            "summary": "未生成视觉匹配结果。",
        }

    best_overall = max(best_candidates, key=lambda candidate: candidate.get("confidence", 0))
    average_points = round(
        sum(candidate.get("matched_points", 0) for candidate in best_candidates) / len(best_candidates),
        1,
    )
    needs_review_count = sum(
        1
        for candidate in best_candidates
        if candidate.get("confidence", 0) < 0.5 or candidate.get("status") == "needs_review"
    )
    geometry_verified = all(candidate.get("inlier_ratio", 0) >= 0.3 for candidate in best_candidates)
    summary = (
        f"已汇总 {len(results)} 张视觉样例，最高置信候选为 {best_overall['tile_id']} "
        f"({round(best_overall['confidence'] * 100)}%)。"
    )
    if needs_review_count:
        summary += f" 其中 {needs_review_count} 张需要人工复核。"
    return {
        "image_count": len(list_query_images(task_id)),
        "matched_image_count": len(results),
        "best_tile_id": best_overall["tile_id"],
        "best_confidence": best_overall["confidence"],
        "average_matched_points": average_points,
        "geometry_verified": geometry_verified,
        "needs_review_count": needs_review_count,
        "summary": summary,
    }


def build_vision_event(match_result: dict, capture_time_s: int | None = None) -> dict:
    best = _best_candidate(match_result)
    if not best:
        return {
            "time_s": capture_time_s or 0,
            "type": "vision_match",
            "title": "视觉匹配无候选",
            "description": f"{match_result.get('image_id', 'unknown')} 未返回有效候选区。",
            "position": [0, 0, 0],
        }
    confidence = round(best.get("confidence", 0) * 100)
    needs_review = best.get("confidence", 0) < 0.5 or best.get("status") == "needs_review"
    title = "视觉匹配需要复核" if needs_review else "视觉匹配完成"
    return {
        "time_s": capture_time_s if capture_time_s is not None else 0,
        "type": "vision_match",
        "title": title,
        "description": (
            f"输入 {match_result.get('image_id')} 的最优候选为 {best['tile_id']}，"
            f"置信度 {confidence}%，匹配点 {best.get('matched_points', 0)}。"
        ),
        "position": best.get("center", [0, 0, 0]),
    }


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


def _best_candidate(match_result: dict) -> dict | None:
    candidates = match_result.get("candidates", [])
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate.get("confidence", 0))
