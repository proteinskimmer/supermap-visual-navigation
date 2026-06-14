from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.synthetic_view_service import localize_with_synthetic_views  # noqa: E402
from app.services.vision_matcher_provider import V05_EVIDENCE_DIR, matcher_runtime_status  # noqa: E402
from app.services.vision_service import list_query_images  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate v0.5 OpenCV visual matching evidence.")
    parser.add_argument("--task-id", default="task_001")
    parser.add_argument("--top-k-tiles", type=int, default=2)
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--matcher-mode", default="opencv_auto")
    args = parser.parse_args()

    V05_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    status = matcher_runtime_status()
    images = list_query_images(args.task_id)[: args.limit]
    results = []
    for image in images:
        localization = localize_with_synthetic_views(
            task_id=args.task_id,
            image_id=image["id"],
            top_k_tiles=args.top_k_tiles,
            matcher_mode=args.matcher_mode,
        )
        results.append(
            {
                "image_id": image["id"],
                "frame_trigger": image.get("frame_trigger", ""),
                "provider": localization["provider"],
                "selected_provider": localization.get("selected_provider", ""),
                "status": localization["status"],
                "matched_points": localization["matched_points"],
                "inlier_ratio": localization["inlier_ratio"],
                "confidence": localization["confidence"],
                "error_radius_m": localization["error_radius_m"],
                "failure_reason": localization["failure_reason"],
                "best_estimated_pose": localization["best_estimated_pose"],
                "match_count": len(localization["matches"]),
            }
        )

    summary = {
        "task_id": args.task_id,
        "provider": args.matcher_mode,
        "matcher_status": status.get(args.matcher_mode, {}),
        "evidence_dir": str(V05_EVIDENCE_DIR),
        "image_count": len(images),
        "localized_count": sum(1 for item in results if item["status"] == "localized"),
        "results": results,
    }
    summary_path = V05_EVIDENCE_DIR / f"summary_{args.matcher_mode}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
