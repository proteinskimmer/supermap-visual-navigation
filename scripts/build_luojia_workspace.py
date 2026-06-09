import argparse
import json
from pathlib import Path

from iobjectspy.conversion import import_shape, import_tif
from iobjectspy.data import DatasourceConnectionInfo, Workspace, WorkspaceConnectionInfo
from iobjectspy.enums import EngineType, ImportMode, WorkspaceType
from iobjectspy.mapping import Map


INPUTS = [
    {
        "kind": "raster",
        "path": "raw_test_data/珞珈山影像.tif",
        "dataset": "luojia_ortho",
        "options": {"is_import_as_grid": False, "is_build_pyramid": True},
    },
    {
        "kind": "raster",
        "path": "raw_student_output/珞珈山DEM.tif",
        "dataset": "luojia_dem",
        "options": {"is_import_as_grid": True, "is_build_pyramid": True},
    },
    {
        "kind": "shape",
        "path": "raw_student_output/区域地形点.shp",
        "dataset": "luojia_terrain_points",
        "options": {"is_import_as_3d": True, "source_file_charset": "UTF-8"},
    },
    {
        "kind": "shape",
        "path": "raw_student_output/珞珈山周边建筑3D.shp",
        "dataset": "luojia_buildings_3d",
        "options": {"is_import_as_3d": False, "source_file_charset": "UTF-8"},
    },
]


def parse_args():
    parser = argparse.ArgumentParser(description="Build Luojia Mountain SuperMap workspace from TIF/SHP data.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--source-dir", default="data_sources/luojia_mountain")
    parser.add_argument("--workspace", default="supermap_file_root/luojia_workspace/luojia_mountain_demo.smwu")
    parser.add_argument("--datasource", default="supermap_file_root/luojia_workspace/luojia_mountain_demo.udbx")
    parser.add_argument("--datasource-alias", default="luojia_mountain_demo")
    parser.add_argument("--map-name", default="luojia_mountain_map")
    parser.add_argument("--summary", default="supermap_file_root/luojia_workspace/build_summary.json")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def remove_existing(path: Path):
    if path.exists():
        path.unlink()
    for sidecar in [path.with_suffix(".udd"), path.with_suffix(".xml")]:
        if sidecar.exists():
            sidecar.unlink()


def ensure_inputs(source_dir: Path):
    missing = []
    for item in INPUTS:
        path = source_dir / item["path"]
        if not path.exists():
            missing.append(str(path))
    if missing:
        raise FileNotFoundError("Missing Luojia source files: " + ", ".join(missing))


def import_one(item, source_dir: Path, datasource):
    source = source_dir / item["path"]
    dataset_name = item["dataset"]
    if item["kind"] == "raster":
        return import_tif(
            str(source),
            datasource,
            out_dataset_name=dataset_name,
            **item["options"],
        )
    if item["kind"] == "shape":
        return import_shape(
            str(source),
            datasource,
            out_dataset_name=dataset_name,
            import_mode=ImportMode.OVERWRITE,
            **item["options"],
        )
    raise ValueError(f"Unsupported input kind: {item['kind']}")


def dataset_names_from_result(result):
    names = []
    if result is None:
        return names
    if not isinstance(result, (list, tuple)):
        result = [result]
    for dataset in result:
        name = getattr(dataset, "name", None)
        names.append(name or str(dataset))
    return names


def main():
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    source_dir = (project_root / args.source_dir).resolve()
    workspace_path = (project_root / args.workspace).resolve()
    datasource_path = (project_root / args.datasource).resolve()
    summary_path = (project_root / args.summary).resolve()

    ensure_inputs(source_dir)
    workspace_path.parent.mkdir(parents=True, exist_ok=True)
    datasource_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    if args.overwrite:
        remove_existing(workspace_path)
        remove_existing(datasource_path)
    elif workspace_path.exists() or datasource_path.exists():
        raise FileExistsError("Target Luojia workspace or datasource already exists. Re-run with --overwrite.")

    workspace = Workspace().create(WorkspaceConnectionInfo(str(workspace_path), WorkspaceType.SMWU))

    imported = []
    try:
        datasource = workspace.create_datasource(
            DatasourceConnectionInfo(
                server=str(datasource_path),
                engine_type=EngineType.UDBX,
                alias=args.datasource_alias,
            )
        )

        for item in INPUTS:
            result = import_one(item, source_dir, datasource)
            names = dataset_names_from_result(result)
            imported.append(
                {
                    "source": item["path"],
                    "requested_name": item["dataset"],
                    "kind": item["kind"],
                    "imported_names": names,
                }
            )

        map_obj = Map()
        map_layers = []
        for item in imported:
            for dataset_name in item["imported_names"]:
                dataset = datasource.get_dataset(dataset_name)
                if dataset is None:
                    continue
                try:
                    map_obj.add_dataset(dataset)
                    map_layers.append(dataset_name)
                except Exception as exc:
                    map_layers.append(f"{dataset_name} (map add failed: {exc})")

        workspace.add_map(args.map_name, map_obj)
        if not workspace.save():
            raise RuntimeError("workspace.save() returned False")

        summary = {
            "workspace": str(workspace_path),
            "datasource": str(datasource_path),
            "datasource_alias": args.datasource_alias,
            "map_name": args.map_name,
            "inputs": imported,
            "map_layer_count": map_obj.get_layers_count(),
            "map_layers": map_layers,
            "map_bounds": str(map_obj.get_bounds()),
        }
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        workspace.close()


if __name__ == "__main__":
    main()
