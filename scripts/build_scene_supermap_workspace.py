import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Build a SuperMap workspace from a scene data profile.")
    parser.add_argument("--config", required=True, help="Scene data profile JSON.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def resolve_path(project_root, source_dir, value):
    path = Path(value)
    if path.is_absolute():
        return path
    if source_dir and not str(value).startswith(("frontend/", "supermap_file_root/", "docs/", "config/", "scripts/")):
        return project_root / source_dir / path
    return project_root / path


def remove_existing(path):
    if path.exists():
        path.unlink()
    for sidecar in [path.with_suffix(".udd"), path.with_suffix(".xml")]:
        if sidecar.exists():
            sidecar.unlink()


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
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / config_path
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_dir = Path(config.get("source_dir", ""))
    supermap = config["supermap"]

    workspace_path = resolve_path(project_root, "", supermap["workspace"])
    datasource_path = resolve_path(project_root, "", supermap["datasource"])
    summary_path = resolve_path(project_root, "", supermap.get("summary", "supermap_file_root/build_scene_summary.json"))

    missing = []
    for item in supermap.get("imports", []):
        source = resolve_path(project_root, source_dir, item["path"])
        if not source.exists():
            missing.append(str(source))
    if missing:
        raise FileNotFoundError("Missing source files: " + ", ".join(missing))

    workspace_path.parent.mkdir(parents=True, exist_ok=True)
    datasource_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    if args.overwrite:
        remove_existing(workspace_path)
        remove_existing(datasource_path)
    elif workspace_path.exists() or datasource_path.exists():
        raise FileExistsError("Target workspace or datasource already exists. Re-run with --overwrite.")

    from iobjectspy.conversion import import_shape, import_tif
    from iobjectspy.data import DatasourceConnectionInfo, Workspace, WorkspaceConnectionInfo
    from iobjectspy.enums import EngineType, ImportMode, WorkspaceType
    from iobjectspy.mapping import Map

    workspace = Workspace().create(WorkspaceConnectionInfo(str(workspace_path), WorkspaceType.SMWU))
    imported = []
    try:
        datasource = workspace.create_datasource(
            DatasourceConnectionInfo(
                server=str(datasource_path),
                engine_type=EngineType.UDBX,
                alias=supermap.get("datasource_alias", config["scene_id"]),
            )
        )

        for item in supermap.get("imports", []):
            source = resolve_path(project_root, source_dir, item["path"])
            options = dict(item.get("options", {}))
            if item["kind"] == "raster":
                result = import_tif(str(source), datasource, out_dataset_name=item["dataset"], **options)
            elif item["kind"] == "shape":
                result = import_shape(
                    str(source),
                    datasource,
                    out_dataset_name=item["dataset"],
                    import_mode=ImportMode.OVERWRITE,
                    **options,
                )
            else:
                raise ValueError(f"Unsupported import kind: {item['kind']}")
            imported.append(
                {
                    "source": item["path"],
                    "dataset": item["dataset"],
                    "kind": item["kind"],
                    "add_to_map": bool(item.get("add_to_map", True)),
                    "imported_names": dataset_names_from_result(result),
                }
            )

        map_obj = Map()
        map_layers = []
        for item in imported:
            if not item["add_to_map"]:
                continue
            for dataset_name in item["imported_names"]:
                dataset = datasource.get_dataset(dataset_name)
                if dataset is None:
                    continue
                try:
                    map_obj.add_dataset(dataset)
                    map_layers.append(dataset_name)
                except Exception as exc:
                    map_layers.append(f"{dataset_name} (map add failed: {exc})")

        workspace.add_map(supermap.get("map_name", f"{config['scene_id']}_map"), map_obj)
        if not workspace.save():
            raise RuntimeError("workspace.save() returned False")

        summary = {
            "scene_id": config["scene_id"],
            "workspace": str(workspace_path),
            "datasource": str(datasource_path),
            "datasource_alias": supermap.get("datasource_alias", config["scene_id"]),
            "map_name": supermap.get("map_name", f"{config['scene_id']}_map"),
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
