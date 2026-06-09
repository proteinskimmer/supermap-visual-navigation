import argparse
import json
from pathlib import Path

from iobjectspy.conversion import import_geojson
from iobjectspy.data import DatasourceConnectionInfo, Workspace, WorkspaceConnectionInfo
from iobjectspy.enums import EngineType, ImportMode, WorkspaceType
from iobjectspy.mapping import Map


REQUIRED_GEOJSON = [
    ("task_area.geojson", "task_area"),
    ("risk_zone.geojson", "risk_zone"),
    ("obstacle.geojson", "obstacle"),
    ("vision_tile.geojson", "vision_tile"),
    ("start_target.geojson", "start_target"),
    ("routes_preview.geojson", "routes_preview"),
    ("vision_image_center.geojson", "vision_image_center"),
    ("uav_position.geojson", "uav_position"),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Build low_altitude_demo SuperMap workspace from GeoJSON.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--geojson-dir", default="demo_data/gis_export")
    parser.add_argument("--workspace", default="supermap_file_root/demo_workspace_auto/low_altitude_demo.smwu")
    parser.add_argument("--datasource", default="supermap_file_root/demo_workspace_auto/low_altitude_demo.udbx")
    parser.add_argument("--datasource-alias", default="low_altitude_demo")
    parser.add_argument("--map-name", default="low_altitude_demo_map")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--summary", default="supermap_file_root/demo_workspace_auto/build_summary.json")
    return parser.parse_args()


def remove_existing(path: Path):
    if path.exists():
        path.unlink()
    sidecars = []
    if path.suffix.lower() == ".udbx":
        sidecars.append(path.with_suffix(".udd"))
    if path.suffix.lower() == ".udb":
        sidecars.append(path.with_suffix(".udd"))
    for sidecar in sidecars:
        if sidecar.exists():
            sidecar.unlink()


def ensure_inputs(geojson_dir: Path):
    missing = []
    for filename, _ in REQUIRED_GEOJSON:
        path = geojson_dir / filename
        if not path.exists():
            missing.append(str(path))
            continue
        with path.open("r", encoding="utf-8-sig") as file:
            payload = json.load(file)
        if payload.get("type") != "FeatureCollection" or not payload.get("features"):
            raise RuntimeError(f"{path} is not a non-empty GeoJSON FeatureCollection")
    if missing:
        raise FileNotFoundError("Missing GeoJSON files: " + ", ".join(missing))


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    geojson_dir = (project_root / args.geojson_dir).resolve()
    workspace_path = (project_root / args.workspace).resolve()
    datasource_path = (project_root / args.datasource).resolve()
    summary_path = (project_root / args.summary).resolve()

    ensure_inputs(geojson_dir)
    workspace_path.parent.mkdir(parents=True, exist_ok=True)
    datasource_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    if args.overwrite:
        remove_existing(workspace_path)
        remove_existing(datasource_path)
    elif workspace_path.exists() or datasource_path.exists():
        raise FileExistsError("Target workspace or datasource already exists. Re-run with --overwrite.")

    ws_conn = WorkspaceConnectionInfo(str(workspace_path), WorkspaceType.SMWU)
    workspace = Workspace().create(ws_conn)

    imported = []
    try:
        ds_conn = DatasourceConnectionInfo(
            server=str(datasource_path),
            engine_type=EngineType.UDBX,
            alias=args.datasource_alias,
        )
        datasource = workspace.create_datasource(ds_conn)

        for filename, dataset_name in REQUIRED_GEOJSON:
            result = import_geojson(
                str(geojson_dir / filename),
                datasource,
                out_dataset_name=dataset_name,
                import_mode=ImportMode.OVERWRITE,
                source_file_charset="UTF-8",
            )
            for dataset in result:
                imported.append(getattr(dataset, "name", str(dataset)))

        map_obj = Map()
        for dataset_name in imported:
            dataset = datasource.get_dataset(dataset_name)
            if dataset is None:
                raise RuntimeError(f"Imported dataset not found: {dataset_name}")
            map_obj.add_dataset(dataset)

        workspace.add_map(args.map_name, map_obj)
        if not workspace.save():
            raise RuntimeError("workspace.save() returned False")

        summary = {
            "workspace": str(workspace_path),
            "datasource": str(datasource_path),
            "datasource_alias": args.datasource_alias,
            "map_name": args.map_name,
            "dataset_count": len(imported),
            "dataset_names": imported,
            "map_layer_count": map_obj.get_layers_count(),
            "map_bounds": str(map_obj.get_bounds()),
        }
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        workspace.close()


if __name__ == "__main__":
    main()
