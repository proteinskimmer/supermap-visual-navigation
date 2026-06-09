import argparse
import json
from pathlib import Path

from iobjectspy.data import Workspace, WorkspaceConnectionInfo
from iobjectspy.enums import WorkspaceType
from iobjectspy.mapping import Map


def parse_args():
    parser = argparse.ArgumentParser(description="Render low_altitude_demo_map from a SuperMap workspace.")
    parser.add_argument("--project-root", default="E:/supermap_project")
    parser.add_argument("--workspace", default="supermap_file_root/demo_workspace/low_altitude_demo.smwu")
    parser.add_argument("--map-name", default="low_altitude_demo_map")
    parser.add_argument("--output", default="docs/delivery/screenshots/low_altitude_demo_map_iobjectspy_preview.png")
    parser.add_argument("--summary", default="docs/delivery/screenshots/low_altitude_demo_map_iobjectspy_preview.json")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=1000)
    return parser.parse_args()


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    workspace_path = (project_root / args.workspace).resolve()
    output_path = (project_root / args.output).resolve()
    summary_path = (project_root / args.summary).resolve()

    if not workspace_path.exists():
        raise FileNotFoundError(f"Workspace not found: {workspace_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    workspace = None
    map_obj = Map()
    try:
        ws_conn = WorkspaceConnectionInfo(str(workspace_path), WorkspaceType.SMWU)
        workspace = Workspace().open(ws_conn)
        if workspace is None:
            raise RuntimeError(f"Failed to open workspace: {workspace_path}")

        maps = list(workspace.get_maps())
        map_names = [item.get_name() for item in maps]
        if args.map_name not in map_names:
            raise RuntimeError(f"Map {args.map_name!r} not found in workspace. Available maps: {map_names}")

        map_obj = maps[map_names.index(args.map_name)]
        if map_obj is None:
            raise RuntimeError(f"Failed to get map: {args.map_name}")

        map_obj.set_image_size(args.width, args.height)
        map_obj.view_entire()
        if not map_obj.output_to_file(str(output_path), image_size=(args.width, args.height)):
            raise RuntimeError(f"Failed to output map preview: {output_path}")

        summary = {
            "workspace": str(workspace_path),
            "map_name": args.map_name,
            "output": str(output_path),
            "image_size": [args.width, args.height],
            "map_layer_count": map_obj.get_layers_count(),
            "map_bounds": str(map_obj.get_bounds()),
            "strict_status": "iObjectSpy rendered project map preview; this is script evidence, not an iDesktopX GUI screenshot.",
        }
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        try:
            map_obj.close()
        except Exception:
            pass
        if workspace is not None:
            workspace.close()


if __name__ == "__main__":
    main()
