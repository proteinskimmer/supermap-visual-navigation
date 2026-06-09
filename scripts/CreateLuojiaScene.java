import com.supermap.data.Dataset;
import com.supermap.data.DatasetGrid;
import com.supermap.data.DatasetType;
import com.supermap.data.Datasource;
import com.supermap.data.Datasets;
import com.supermap.data.PrjCoordSys;
import com.supermap.data.Workspace;
import com.supermap.data.WorkspaceConnectionInfo;
import com.supermap.data.WorkspaceType;
import com.supermap.realspace.Camera;
import com.supermap.realspace.Layer3DSettingGrid;
import com.supermap.realspace.Layer3DSettingImage;
import com.supermap.realspace.Layer3DSettingVector;
import com.supermap.realspace.Scene;
import com.supermap.realspace.SceneType;
import com.supermap.realspace.TerrainLayer;

public class CreateLuojiaScene {
    public static void main(String[] args) {
        if (args.length < 1) {
            throw new IllegalArgumentException("Usage: CreateLuojiaScene <workspace.smwu> [sceneName] [datasourceAlias]");
        }

        String workspacePath = args[0];
        String sceneName = args.length >= 2 ? args[1] : "luojia_mountain_demo";
        String datasourceAlias = args.length >= 3 ? args[2] : "luojia_mountain_demo";

        Workspace workspace = new Workspace();
        try {
            WorkspaceConnectionInfo info = new WorkspaceConnectionInfo();
            info.setType(WorkspaceType.SMWU);
            info.setServer(workspacePath);

            if (!workspace.open(info)) {
                throw new IllegalStateException("Failed to open workspace: " + workspacePath);
            }

            Datasource datasource = workspace.getDatasources().get(datasourceAlias);
            if (datasource == null) {
                throw new IllegalStateException("Datasource not found: " + datasourceAlias);
            }

            int existing = workspace.getScenes().indexOf(sceneName);
            if (existing >= 0 && !workspace.getScenes().remove(existing)) {
                throw new IllegalStateException("Failed to remove existing scene: " + sceneName);
            }

            Scene scene = new Scene(workspace);
            scene.setName(sceneName);
            scene.setSceneType(SceneType.GLOBE);
            scene.setPrjCoordSys(PrjCoordSys.fromEPSG(4547));
            scene.setCamera(new Camera(114.364, 30.556, 1800.0));
            scene.setTerrainExaggeration(1.0);

            int addedTerrain = 0;
            int addedLayers = 0;
            Datasets datasets = datasource.getDatasets();
            for (int i = 0; i < datasets.getCount(); i++) {
                Dataset dataset = datasets.get(i);
                String name = dataset.getName();
                DatasetType type = dataset.getType();
                try {
                    if (type == DatasetType.GRID && name.toLowerCase().contains("dem")) {
                        TerrainLayer terrainLayer = scene.getTerrainLayers().add((DatasetGrid) dataset, true, name + "_terrain");
                        if (terrainLayer != null) {
                            addedTerrain++;
                            System.out.println("added_terrain=" + name);
                        }
                        Layer3DSettingGrid gridSetting = new Layer3DSettingGrid();
                        gridSetting.setOpaqueRate(35);
                        if (scene.getLayers().add(dataset, gridSetting, true, name + "_grid") != null) {
                            addedLayers++;
                            System.out.println("added_grid_layer=" + name);
                        }
                    } else if (type == DatasetType.IMAGE) {
                        Layer3DSettingImage imageSetting = new Layer3DSettingImage();
                        imageSetting.setOpaqueRate(100);
                        if (scene.getLayers().add(dataset, imageSetting, true, name) != null) {
                            addedLayers++;
                            System.out.println("added_image_layer=" + name);
                        }
                    } else if (type == DatasetType.REGION || type == DatasetType.REGION3D
                            || type == DatasetType.POINT || type == DatasetType.POINT3D
                            || type == DatasetType.LINE || type == DatasetType.LINE3D) {
                        Layer3DSettingVector vectorSetting = new Layer3DSettingVector();
                        if (name.toLowerCase().contains("building")) {
                            vectorSetting.setExtendedHeightField("HEIGHT_M");
                        }
                        if (scene.getLayers().add(dataset, vectorSetting, true, name) != null) {
                            addedLayers++;
                            System.out.println("added_vector_layer=" + name + ", type=" + type);
                        }
                    } else {
                        System.out.println("skipped_dataset=" + name + ", type=" + type);
                    }
                } catch (Throwable ex) {
                    System.out.println("add_failed=" + name + ", type=" + type + " :: " + ex.getClass().getName() + " :: " + ex.getMessage());
                }
            }

            String xml = scene.toXML();
            if (xml == null || xml.trim().isEmpty()) {
                throw new IllegalStateException("Scene.toXML returned empty XML");
            }
            int addedIndex = workspace.getScenes().add(sceneName, xml);
            if (addedIndex < 0) {
                throw new IllegalStateException("Scenes.add returned " + addedIndex);
            }
            if (!workspace.save()) {
                throw new IllegalStateException("Workspace.save returned false");
            }

            System.out.println("scene_xml_length=" + xml.length());
            System.out.println("added_terrain_count=" + addedTerrain);
            System.out.println("added_layer_count=" + addedLayers);
            System.out.println("added_scene_index=" + addedIndex);
            System.out.println("after_scene_count=" + workspace.getScenes().getCount());
            System.out.println("after_scene_index=" + workspace.getScenes().indexOf(sceneName));
        } finally {
            workspace.close();
            workspace.dispose();
        }
    }
}
