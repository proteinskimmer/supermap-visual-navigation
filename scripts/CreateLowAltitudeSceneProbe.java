import com.supermap.data.Dataset;
import com.supermap.data.Datasource;
import com.supermap.data.PrjCoordSys;
import com.supermap.data.Scenes;
import com.supermap.data.Workspace;
import com.supermap.data.WorkspaceConnectionInfo;
import com.supermap.data.WorkspaceType;
import com.supermap.realspace.Camera;
import com.supermap.realspace.Layer3DSettingVector;
import com.supermap.realspace.Scene;
import com.supermap.realspace.SceneType;

public class CreateLowAltitudeSceneProbe {
    private static final String[] DATASETS = {
        "task_area_R",
        "risk_zone_R",
        "obstacle_ZP",
        "vision_tile_R",
        "start_target_ZP",
        "routes_preview_ZL",
        "vision_image_center_ZP",
        "uav_position_ZP"
    };

    public static void main(String[] args) {
        if (args.length < 1) {
            throw new IllegalArgumentException("Usage: CreateLowAltitudeSceneProbe <workspace.smwu> [sceneName]");
        }

        String workspacePath = args[0];
        String sceneName = args.length >= 2 ? args[1] : "low_altitude_demo";

        Workspace workspace = new Workspace();
        try {
            WorkspaceConnectionInfo info = new WorkspaceConnectionInfo();
            info.setType(WorkspaceType.SMWU);
            info.setServer(workspacePath);

            if (!workspace.open(info)) {
                throw new IllegalStateException("Failed to open workspace: " + workspacePath);
            }

            Scenes scenes = workspace.getScenes();
            System.out.println("before_scene_count=" + scenes.getCount());
            for (int i = 0; i < scenes.getCount(); i++) {
                System.out.println("before_scene_" + i + "=" + scenes.get(i));
            }

            int existing = scenes.indexOf(sceneName);
            if (existing >= 0 && !scenes.remove(existing)) {
                throw new IllegalStateException("Failed to remove existing scene: " + sceneName);
            }

            Scene scene = new Scene(workspace);
            scene.setName(sceneName);
            scene.setSceneType(SceneType.GLOBE);
            scene.setPrjCoordSys(PrjCoordSys.fromEPSG(4326));
            scene.setCamera(new Camera(116.17, 39.16, 12000.0));

            Datasource datasource = workspace.getDatasources().get("low_altitude_demo");
            if (datasource == null) {
                throw new IllegalStateException("Datasource not found: low_altitude_demo");
            }

            int addedLayers = 0;
            for (String datasetName : DATASETS) {
                Dataset dataset = datasource.getDatasets().get(datasetName);
                if (dataset == null) {
                    System.out.println("missing_dataset=" + datasetName);
                    continue;
                }
                try {
                    if (scene.getLayers().add(dataset, new Layer3DSettingVector(), true) != null) {
                        addedLayers++;
                        System.out.println("added_layer=" + datasetName);
                    }
                } catch (Throwable ex) {
                    System.out.println("add_layer_failed=" + datasetName + " :: " + ex.getClass().getName() + " :: " + ex.getMessage());
                }
            }

            String xml = scene.toXML();
            if (xml == null || xml.trim().isEmpty()) {
                throw new IllegalStateException("Scene.toXML returned empty XML");
            }
            int addedIndex = scenes.add(sceneName, xml);
            if (addedIndex < 0) {
                throw new IllegalStateException("Scenes.add returned " + addedIndex);
            }
            if (!workspace.save()) {
                throw new IllegalStateException("Workspace.save returned false");
            }

            System.out.println("scene_xml_length=" + xml.length());
            System.out.println("added_layers=" + addedLayers);
            System.out.println("added_scene_index=" + addedIndex);
            System.out.println("after_scene_count=" + scenes.getCount());
            System.out.println("after_scene_index=" + scenes.indexOf(sceneName));
        } finally {
            workspace.close();
            workspace.dispose();
        }
    }
}
