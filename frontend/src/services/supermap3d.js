const DEFAULT_SDK_BASE = "/vendor/supermap3d/Build/SuperMap3D";
const CURRENT_POINT_PREFIX = "demo-current-uav";
const CURRENT_UAV_MODEL_NAME = "demo-current-uav-model";
const FLIGHT_PATH_MIN_HEIGHT = 192;
const UAV_MODEL_MIN_HEIGHT = 212;
const UAV_SHADOW_HEIGHT = 8;
const UAV_MODEL_URL = "/demo/models/drone_animated.glb";
const UAV_MODEL_SCALE = 0.16;
const UAV_MODEL_MIN_PIXEL_SIZE = 58;
const UAV_MODEL_MAXIMUM_SCALE = 80;
const UAV_MODEL_HEADING_OFFSET = Math.PI / 2;
const UAV_POSITION_SMOOTHING = 0.22;
const UAV_HEADING_SMOOTHING = 0.18;
const UAV_HEADING_DEADBAND_DEG = 3;
const UAV_RENDER_SNAP_DISTANCE = 220;
const TASK_MARKER_HEIGHT = 236;
const TASK_MARKER_RING_HEIGHT = 10;
const LUOJIA_STATIC_ORTHO = {
  url: "/demo/luojia_ortho_preview.jpg",
  // Bounds are transformed from the ortho TIFF world file in EPSG:4547.
  west: 114.35606090027636,
  south: 30.53350272802454,
  east: 114.3721388967706,
  north: 30.541036539119585,
  relativeHeight: 4,
  absoluteSafetyHeight: 165,
};

const LUOJIA_REGIONAL_CONTEXT = {
  west: 114.315,
  south: 30.505,
  east: 114.415,
  north: 30.575,
  baseHeight: -12,
  heightScale: 90,
  cols: 48,
  rows: 36,
};

let sdkPromise = null;

export function detectWebGL2() {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("webgl2");
  return Boolean(context);
}

export async function loadSuperMap3D(options = {}) {
  if (window.SuperMap3D) return window.SuperMap3D;
  if (sdkPromise) return sdkPromise;

  const sdkBase = normalizeBase(options.sdkBase || import.meta.env.VITE_SUPERMAP_SDK_BASE || DEFAULT_SDK_BASE);
  window.CESIUM_BASE_URL = `${sdkBase}/`;
  window.SUPERMAP3D_BASE_URL = `${sdkBase}/`;

  sdkPromise = Promise.all([
    loadCss(`${sdkBase}/Widgets/widgets.css`),
    loadScript(`${sdkBase}/SuperMap3D.js`),
  ]).then(() => {
    if (!window.SuperMap3D) {
      throw new Error("SuperMap3D.js loaded but window.SuperMap3D is not available");
    }
    return window.SuperMap3D;
  });

  return sdkPromise;
}

export function createViewer(container, SuperMap3D, options = {}) {
  const contextType = options.contextType ?? 2;
  const viewer = new SuperMap3D.Viewer(container, {
    animation: false,
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    infoBox: false,
    sceneModePicker: false,
    selectionIndicator: false,
    timeline: false,
    navigationHelpButton: false,
    contextOptions: {
      contextType,
      webgl: {
        alpha: true,
        antialias: true,
        preserveDrawingBuffer: true,
        failIfMajorPerformanceCaveat: false,
      },
    },
  });

  if (viewer.scene?.screenSpaceCameraController) {
    viewer.scene.screenSpaceCameraController.inertiaZoom = 0.28;
    viewer.scene.screenSpaceCameraController.inertiaTranslate = 0.22;
    viewer.scene.screenSpaceCameraController.inertiaSpin = 0.18;
    viewer.scene.screenSpaceCameraController.maximumMovementRatio = 0.06;
  }
  try {
    if (viewer.scene && SuperMap3D.Color?.TRANSPARENT) {
      viewer.scene.backgroundColor = SuperMap3D.Color.TRANSPARENT;
    }
  } catch (error) {
    console.warn("Failed to set transparent SuperMap background", error);
  }

  return viewer;
}

export function isLuojiaSuperMapConfig(supermapConfig) {
  return isLuojiaScene(supermapConfig);
}

export async function openScene(viewer, sceneUrl) {
  if (!sceneUrl) return null;
  const scene = await getScene(viewer);
  if (!scene?.open) {
    throw new Error("SuperMap scene.open is not available on this Viewer");
  }
  return scene.open(sceneUrl);
}

export function clearDemoEntities(viewer) {
  if (!viewer?.entities) return;
  const entities = viewer.entities.values || [];
  [...entities]
    .filter((entity) => {
      if (entity?.name === CURRENT_UAV_MODEL_NAME) return false;
      return entity?.properties?.supermapDemo === true || entity?.name?.startsWith("demo-");
    })
    .forEach((entity) => viewer.entities.remove(entity));
}

export function drawDemoOverlay(viewer, SuperMap3D, data) {
  if (!viewer || !SuperMap3D) return;
  clearDemoEntities(viewer);
  const visibility = buildLayerVisibility(data.layers || []);
  const useRealSuperMapScene = hasRealSuperMapScene(data);
  if (visibility.terrain && data.luojiaTerrain) {
    drawRegionalTerrainContext(viewer, SuperMap3D, data.luojiaTerrain, data.supermapConfig);
  }
  if (visibility.imagery && data.luojiaTerrain) {
    drawLuojiaTerrainSurface(viewer, SuperMap3D, data.luojiaTerrain);
  }
  if (visibility.obstacle) {
    if (useRealSuperMapScene && data.luojiaBuildings?.length) {
      drawLuojiaBuildings(viewer, SuperMap3D, data.luojiaBuildings, data.luojiaTerrain);
    } else if (!useRealSuperMapScene) {
      drawDemoBuildings(viewer, SuperMap3D, data.selectedTask, data.taskDetail?.obstacles || []);
    }
  }
  if (visibility.risk_zone) {
    drawRiskZones(viewer, SuperMap3D, data.taskDetail?.risk_zones || []);
    drawTemporaryRisk(viewer, SuperMap3D, data.temporaryRisk);
  }
  if (visibility.imagery) {
    drawVisionTiles(viewer, SuperMap3D, data.visionTiles || []);
    drawVisionCandidates(viewer, SuperMap3D, data.visionResult?.candidates || []);
  }
  drawRoutes(viewer, SuperMap3D, data.routes || [], data.selectedRoute, data.replannedRoute);
  drawTaskPoints(viewer, SuperMap3D, data.selectedTask);
}

export function updateVisionCandidates(viewer, SuperMap3D, candidates = []) {
  if (!viewer || !SuperMap3D) return;
  clearDemoEntitiesByPrefix(viewer, "demo-vision-candidate");
  drawVisionCandidates(viewer, SuperMap3D, candidates);
  viewer.scene?.requestRender?.();
}

export function syncSceneLayerVisibility(viewer, layers = [], supermapConfig = null) {
  if (!viewer?.scene) return;
  cleanupStaleLuojiaFallback(viewer);
  const visibility = buildLayerVisibility(layers);
  if (viewer.__luojiaStaticOrthoEntity) {
    viewer.__luojiaStaticOrthoEntity.show = visibility.imagery;
  }
  if (viewer.__luojiaStaticOrthoSafetyEntity) {
    viewer.__luojiaStaticOrthoSafetyEntity.show = false;
  }
  if (viewer.__luojiaStaticOrthoLayer) {
    viewer.__luojiaStaticOrthoLayer.show = false;
  }
  const mappings = [
    { visible: visibility.imagery, names: [supermapConfig?.layers?.ortho?.dataset, "luojia_ortho", "ortho", "image"] },
    { visible: visibility.terrain, names: [supermapConfig?.layers?.dem?.dataset, "luojia_dem", "Terrain", "terrain"] },
    {
      visible: visibility.obstacle,
      names: [
        supermapConfig?.layers?.buildings_3d?.dataset,
        supermapConfig?.layers?.terrain_points?.dataset,
        "luojia_buildings_3d",
        "luojia_terrain_points",
        "building",
        "point",
      ],
    },
  ];

  const sceneLayers = collectSceneLayers(viewer.scene);
  mappings.forEach((mapping) => {
    const layerVisible = shouldUseStaticOrthoInstead(viewer, supermapConfig, mapping.names) ? false : mapping.visible;
    const directLayers = mapping.names
      .filter(Boolean)
      .map((name) => viewer.scene.layers?.getLayer?.(name) || viewer.scene.layers?.find?.(name))
      .filter(Boolean);
    directLayers.forEach((layer) => setLayerVisible(layer, layerVisible));
    sceneLayers
      .filter((layer) => layerMatchesAnyName(layer, mapping.names))
      .forEach((layer) => setLayerVisible(layer, layerVisible));
  });
  scheduleLayerVisibilityRetry(viewer, layers, supermapConfig);
}

export function installMapImageryFallback(viewer, SuperMap3D, supermapConfig = null) {
  const mapUrl = supermapConfig?.services?.map?.resource_url || "";
  if (!viewer?.imageryLayers) return null;
  const luojiaScene = isLuojiaScene(supermapConfig);

  let mapLayer = null;
  try {
    installOnlineBasemap(viewer, SuperMap3D, supermapConfig);
    installOnlineTerrain(viewer, SuperMap3D, supermapConfig);
    if (!luojiaScene && SuperMap3D?.SuperMapImageryProvider && mapUrl && viewer.__luojiaMapImageryFallbackUrl !== mapUrl) {
      mapLayer = viewer.imageryLayers.addImageryProvider(
        new SuperMap3D.SuperMapImageryProvider({
          url: mapUrl,
        })
      );
      viewer.__luojiaMapImageryFallbackUrl = mapUrl;
      mapLayer.alpha = 0.92;
    }
  } catch (error) {
    console.warn("Failed to add SuperMap map imagery fallback", error);
  }
  return installStaticOrthoFallback(viewer, SuperMap3D, supermapConfig) || mapLayer;
}

export function installOnlineBasemap(viewer, SuperMap3D, supermapConfig = null) {
  const service = supermapConfig?.services?.online_basemap;
  const url = service?.url || "";
  if (!viewer?.imageryLayers || !url) {
    if (viewer) {
      viewer.__onlineBasemap = {
        installed: false,
        status: url ? "unsupported" : "not_configured",
        source: url,
      };
    }
    return null;
  }
  if (viewer.__onlineBasemap?.source === url && viewer.__onlineBasemap?.layer) {
    return viewer.__onlineBasemap.layer;
  }

  try {
    const providerType = service.provider || service.type || "url_template";
    let provider = null;
    if (providerType === "supermap" && SuperMap3D?.SuperMapImageryProvider) {
      provider = new SuperMap3D.SuperMapImageryProvider({ url });
    } else if (SuperMap3D?.UrlTemplateImageryProvider) {
      provider = new SuperMap3D.UrlTemplateImageryProvider({
        url,
        credit: service.credit || service.name || "online basemap",
        minimumLevel: service.minimum_level ?? 0,
        maximumLevel: service.maximum_level ?? 18,
      });
    }
    if (!provider) {
      throw new Error("No supported imagery provider for online basemap");
    }

    const layer = viewer.imageryLayers.addImageryProvider(provider, 0);
    layer.alpha = service.alpha ?? 0.72;
    layer.show = service.visible !== false;
    viewer.__onlineBasemap = {
      installed: true,
      status: "installed",
      source: url,
      provider: providerType,
      layer,
    };
    return layer;
  } catch (error) {
    console.warn("Failed to add online basemap", error);
    viewer.__onlineBasemap = {
      installed: false,
      status: "failed",
      source: url,
      error: error?.message || String(error),
    };
    return null;
  }
}

export function installOnlineTerrain(viewer, SuperMap3D, supermapConfig = null) {
  const service = supermapConfig?.services?.online_terrain;
  const url = service?.url || "";
  if (!viewer || !url) {
    if (viewer) {
      viewer.__onlineTerrain = {
        installed: false,
        status: url ? "unsupported" : "not_configured",
        source: url,
      };
    }
    return null;
  }
  if (viewer.__onlineTerrain?.source === url && viewer.__onlineTerrain?.provider) {
    return viewer.__onlineTerrain.provider;
  }

  try {
    let provider = null;
    if (SuperMap3D?.SuperMapTerrainProvider) {
      provider = new SuperMap3D.SuperMapTerrainProvider({ url });
    } else if (SuperMap3D?.CesiumTerrainProvider) {
      provider = new SuperMap3D.CesiumTerrainProvider({ url });
    }
    if (!provider) {
      throw new Error("No supported terrain provider for online terrain");
    }
    if ("terrainProvider" in viewer) {
      viewer.terrainProvider = provider;
    } else if (viewer.scene?.globe) {
      viewer.scene.globe.terrainProvider = provider;
    }
    viewer.__onlineTerrain = {
      installed: true,
      status: "installed",
      source: url,
      provider,
    };
    return provider;
  } catch (error) {
    console.warn("Failed to add online terrain", error);
    viewer.__onlineTerrain = {
      installed: false,
      status: "failed",
      source: url,
      error: error?.message || String(error),
    };
    return null;
  }
}

function installStaticOrthoFallback(viewer, SuperMap3D, supermapConfig = null) {
  if (!isLuojiaScene(supermapConfig) || !SuperMap3D?.Rectangle) return null;
  cleanupStaleLuojiaFallback(viewer);
  if (viewer.__luojiaStaticOrthoEntity) return viewer.__luojiaStaticOrthoEntity;

  try {
    prepareLuojiaViewer(viewer, SuperMap3D);
    const rectangle = SuperMap3D.Rectangle.fromDegrees(
      LUOJIA_STATIC_ORTHO.west,
      LUOJIA_STATIC_ORTHO.south,
      LUOJIA_STATIC_ORTHO.east,
      LUOJIA_STATIC_ORTHO.north
    );
    const entity = viewer.entities.add({
      name: "luojia-static-ortho",
      rectangle: {
        coordinates: rectangle,
        material: createImageMaterial(SuperMap3D, LUOJIA_STATIC_ORTHO.url, 0.94),
        height: LUOJIA_STATIC_ORTHO.relativeHeight,
        heightReference: SuperMap3D.HeightReference?.RELATIVE_TO_GROUND || SuperMap3D.HeightReference?.CLAMP_TO_GROUND,
        outline: true,
        outlineColor: colorWithAlpha(SuperMap3D, "WHITE", 0.35),
      },
    });
    viewer.__luojiaStaticOrthoEntity = entity;
    viewer.__luojiaStaticOrthoSafetyEntity = null;
    viewer.__luojiaStaticOrthoLayer = null;
    viewer.__luojiaFallback = {
      installed: true,
      source: LUOJIA_STATIC_ORTHO.url,
      bounds: LUOJIA_STATIC_ORTHO,
      mode: "single-webgl-rectangle",
    };
    return entity;
  } catch (error) {
    console.warn("Failed to add Luojia static ortho fallback", error);
    viewer.__luojiaFallback = {
      installed: false,
      source: LUOJIA_STATIC_ORTHO.url,
      error: error?.message || String(error),
    };
    return null;
  }
}

function drawRegionalTerrainContext(viewer, SuperMap3D, terrain, supermapConfig = null) {
  const bounds = regionalBoundsFromTerrain(terrain);
  if (viewer?.__luojiaRegionalTerrainPrimitive) {
    drawOnlineRegionalImageryTiles(viewer, SuperMap3D, supermapConfig, bounds);
    return;
  }
  if (!viewer?.scene?.primitives) return;
  if (!SuperMap3D.Geometry || !SuperMap3D.Primitive || !SuperMap3D.MaterialAppearance) return;
  const cols = LUOJIA_REGIONAL_CONTEXT.cols;
  const rows = LUOJIA_REGIONAL_CONTEXT.rows;

  try {
    const positions = new Float64Array(cols * rows * 3);
    const st = new Float32Array(cols * rows * 2);
    const indices = [];
    for (let row = 0; row < rows; row += 1) {
      const v = row / (rows - 1);
      const lat = lerp(bounds.north, bounds.south, v);
      for (let col = 0; col < cols; col += 1) {
        const u = col / (cols - 1);
        const lon = lerp(bounds.west, bounds.east, u);
        const height = regionalTerrainHeight(lon, lat, bounds);
        const cartesian = SuperMap3D.Cartesian3.fromDegrees(lon, lat, height);
        const index = row * cols + col;
        positions[index * 3] = cartesian.x;
        positions[index * 3 + 1] = cartesian.y;
        positions[index * 3 + 2] = cartesian.z;
        st[index * 2] = u;
        st[index * 2 + 1] = 1 - v;
      }
    }
    for (let row = 0; row < rows - 1; row += 1) {
      for (let col = 0; col < cols - 1; col += 1) {
        const a = row * cols + col;
        const b = a + 1;
        const c = a + cols;
        const d = c + 1;
        indices.push(a, c, b, b, c, d);
      }
    }

    const geometry = new SuperMap3D.Geometry({
      attributes: new SuperMap3D.GeometryAttributes({
        position: new SuperMap3D.GeometryAttribute({
          componentDatatype: SuperMap3D.ComponentDatatype.DOUBLE,
          componentsPerAttribute: 3,
          values: positions,
        }),
        st: new SuperMap3D.GeometryAttribute({
          componentDatatype: SuperMap3D.ComponentDatatype.FLOAT,
          componentsPerAttribute: 2,
          values: st,
        }),
      }),
      indices: new Uint16Array(indices),
      primitiveType: SuperMap3D.PrimitiveType.TRIANGLES,
      boundingSphere: SuperMap3D.BoundingSphere.fromVertices(positions),
    });
    const material = SuperMap3D.Material.fromType("Color", {
      color: colorWithAlpha(SuperMap3D, "DARKSEAGREEN", 0.28),
    });
    const primitive = new SuperMap3D.Primitive({
      geometryInstances: new SuperMap3D.GeometryInstance({ geometry }),
      appearance: new SuperMap3D.MaterialAppearance({
        material,
        faceForward: true,
        translucent: true,
        closed: false,
      }),
      asynchronous: false,
    });
    viewer.scene.primitives.add(primitive);
    viewer.__luojiaRegionalTerrainPrimitive = primitive;
    viewer.__luojiaRegionalTerrain = {
      installed: true,
      bounds,
      vertices: cols * rows,
      triangles: indices.length / 3,
      mode: "local-regional-context",
    };
    drawOnlineRegionalImageryTiles(viewer, SuperMap3D, supermapConfig, bounds);
  } catch (error) {
    console.warn("Failed to draw Luojia regional terrain context", error);
    viewer.__luojiaRegionalTerrain = {
      installed: false,
      error: error?.message || String(error),
    };
  }
}

function drawOnlineRegionalImageryTiles(viewer, SuperMap3D, supermapConfig, bounds) {
  const service = supermapConfig?.services?.online_basemap;
  const urlTemplate = service?.url || "";
  if (!viewer?.entities || !SuperMap3D?.Rectangle || !urlTemplate.includes("{z}")) {
    return;
  }
  clearDemoEntitiesByPrefix(viewer, "demo-online-regional-imagery");
  const zoom = Math.min(
    service.regional_preview_level ?? 13,
    service.maximum_level ?? 18,
  );
  const westNorth = lonLatToWebMercatorTile(bounds.west, bounds.north, zoom);
  const eastSouth = lonLatToWebMercatorTile(bounds.east, bounds.south, zoom);
  const minX = Math.min(westNorth.x, eastSouth.x);
  const maxX = Math.max(westNorth.x, eastSouth.x);
  const minY = Math.min(westNorth.y, eastSouth.y);
  const maxY = Math.max(westNorth.y, eastSouth.y);
  const maxTiles = service.regional_preview_max_tiles ?? 36;
  let added = 0;

  for (let x = minX; x <= maxX; x += 1) {
    for (let y = minY; y <= maxY; y += 1) {
      if (added >= maxTiles) break;
      const tileBounds = webMercatorTileBounds(x, y, zoom);
      const rectangle = SuperMap3D.Rectangle.fromDegrees(
        Math.max(bounds.west, tileBounds.west),
        Math.max(bounds.south, tileBounds.south),
        Math.min(bounds.east, tileBounds.east),
        Math.min(bounds.north, tileBounds.north),
      );
      viewer.entities.add({
        name: `demo-online-regional-imagery-${zoom}-${x}-${y}`,
        rectangle: {
          coordinates: rectangle,
          material: createImageMaterial(
            SuperMap3D,
            urlTemplate
              .replaceAll("{z}", String(zoom))
              .replaceAll("{x}", String(x))
              .replaceAll("{y}", String(y)),
            service.regional_preview_alpha ?? 0.92,
          ),
          height: LUOJIA_REGIONAL_CONTEXT.baseHeight + 2,
        },
        properties: {
          supermapDemo: true,
          regionalOnlineImagery: true,
        },
      });
      added += 1;
    }
  }

  viewer.__onlineRegionalTileOverlay = {
    installed: added > 0,
    source: urlTemplate,
    provider: service.provider || service.type || "url_template",
    zoom,
    tileCount: added,
  };
}

function drawLuojiaTerrainSurface(viewer, SuperMap3D, terrain) {
  if (!viewer?.scene?.primitives || !terrain?.vertices?.length || !terrain?.indices?.length) return;
  if (viewer.__luojiaTerrainPrimitive) {
    if (viewer.__luojiaStaticOrthoEntity) viewer.__luojiaStaticOrthoEntity.show = false;
    return;
  }
  if (!SuperMap3D.Geometry || !SuperMap3D.Primitive || !SuperMap3D.MaterialAppearance) return;
  try {
    const positions = new Float64Array(terrain.vertices.length * 3);
    const st = new Float32Array(terrain.vertices.length * 2);
    terrain.vertices.forEach((vertex, index) => {
      const cartesian = SuperMap3D.Cartesian3.fromDegrees(vertex.lon, vertex.lat, (vertex.height_m || 0) + 1.5);
      positions[index * 3] = cartesian.x;
      positions[index * 3 + 1] = cartesian.y;
      positions[index * 3 + 2] = cartesian.z;
      st[index * 2] = vertex.u;
      st[index * 2 + 1] = 1 - vertex.v;
    });
    const indices = terrain.vertices.length > 65535 ? new Uint32Array(terrain.indices) : new Uint16Array(terrain.indices);
    const geometry = new SuperMap3D.Geometry({
      attributes: new SuperMap3D.GeometryAttributes({
        position: new SuperMap3D.GeometryAttribute({
          componentDatatype: SuperMap3D.ComponentDatatype.DOUBLE,
          componentsPerAttribute: 3,
          values: positions,
        }),
        st: new SuperMap3D.GeometryAttribute({
          componentDatatype: SuperMap3D.ComponentDatatype.FLOAT,
          componentsPerAttribute: 2,
          values: st,
        }),
      }),
      indices,
      primitiveType: SuperMap3D.PrimitiveType.TRIANGLES,
      boundingSphere: SuperMap3D.BoundingSphere.fromVertices(positions),
    });
    const material = SuperMap3D.Material.fromType("Image", {
      image: terrain.texture || LUOJIA_STATIC_ORTHO.url,
    });
    const primitive = new SuperMap3D.Primitive({
      geometryInstances: new SuperMap3D.GeometryInstance({ geometry }),
      appearance: new SuperMap3D.MaterialAppearance({
        material,
        faceForward: true,
        translucent: false,
        closed: false,
      }),
      asynchronous: false,
    });
    viewer.scene.primitives.add(primitive);
    viewer.__luojiaTerrainPrimitive = primitive;
    if (viewer.__luojiaStaticOrthoEntity) viewer.__luojiaStaticOrthoEntity.show = false;
    viewer.__luojiaTerrainSurface = {
      installed: true,
      vertices: terrain.vertices.length,
      triangles: terrain.indices.length / 3,
      zMin: terrain.z_min,
      zMax: terrain.z_max,
    };
  } catch (error) {
    console.warn("Failed to draw Luojia terrain surface", error);
    viewer.__luojiaTerrainSurface = {
      installed: false,
      error: error?.message || String(error),
    };
  }
}

function regionalBoundsFromTerrain(terrain) {
  const vertices = terrain?.vertices || [];
  if (!vertices.length) return LUOJIA_REGIONAL_CONTEXT;
  const lons = vertices.map((vertex) => vertex.lon);
  const lats = vertices.map((vertex) => vertex.lat);
  const west = Math.min(...lons);
  const east = Math.max(...lons);
  const south = Math.min(...lats);
  const north = Math.max(...lats);
  return {
    west: Math.min(LUOJIA_REGIONAL_CONTEXT.west, west - 0.018),
    south: Math.min(LUOJIA_REGIONAL_CONTEXT.south, south - 0.016),
    east: Math.max(LUOJIA_REGIONAL_CONTEXT.east, east + 0.018),
    north: Math.max(LUOJIA_REGIONAL_CONTEXT.north, north + 0.016),
  };
}

function regionalTerrainHeight(lon, lat, bounds) {
  const u = (lon - bounds.west) / Math.max(0.0001, bounds.east - bounds.west);
  const v = (lat - bounds.south) / Math.max(0.0001, bounds.north - bounds.south);
  const ridge =
    Math.sin(u * Math.PI * 3.2 + 0.4) * 0.38 +
    Math.cos(v * Math.PI * 2.7 - 0.5) * 0.32 +
    Math.sin((u + v) * Math.PI * 4.1) * 0.18;
  const centerBlend = Math.max(0, 1 - Math.hypot(u - 0.5, v - 0.5) * 1.8);
  const broadSlope = (1 - v) * 18 + u * 10;
  return LUOJIA_REGIONAL_CONTEXT.baseHeight + broadSlope + ridge * LUOJIA_REGIONAL_CONTEXT.heightScale * (0.45 + centerBlend * 0.35);
}

function cleanupStaleLuojiaFallback(viewer) {
  try {
    if (viewer?.__luojiaStaticOrthoSafetyEntity) {
      viewer.entities?.remove?.(viewer.__luojiaStaticOrthoSafetyEntity);
      viewer.__luojiaStaticOrthoSafetyEntity = null;
    }
    if (viewer?.__luojiaStaticOrthoLayer) {
      viewer.imageryLayers?.remove?.(viewer.__luojiaStaticOrthoLayer, true);
      viewer.__luojiaStaticOrthoLayer = null;
    }
    const staleEntities = (viewer?.entities?.values || []).filter((entity) => entity?.name === "luojia-static-ortho-safety-plane");
    staleEntities.forEach((entity) => viewer.entities.remove(entity));
  } catch (error) {
    console.warn("Failed to clean stale Luojia fallback layers", error);
  }
}

export function getSuperMapDebugState(viewer, supermapConfig = null) {
  const sceneLayers = collectSceneLayers(viewer?.scene);
  return {
    isLuojia: isLuojiaScene(supermapConfig),
    fallbackInstalled: Boolean(viewer?.__luojiaStaticOrthoEntity),
    fallbackMode: viewer?.__luojiaFallback?.mode || "",
    terrainInstalled: Boolean(viewer?.__luojiaTerrainPrimitive),
    terrainVertices: viewer?.__luojiaTerrainSurface?.vertices || 0,
    terrainTriangles: viewer?.__luojiaTerrainSurface?.triangles || 0,
    regionalTerrainInstalled: Boolean(viewer?.__luojiaRegionalTerrainPrimitive),
    regionalTerrainVertices: viewer?.__luojiaRegionalTerrain?.vertices || 0,
    regionalTerrainTriangles: viewer?.__luojiaRegionalTerrain?.triangles || 0,
    imageryLayerCount: viewer?.imageryLayers?.length ?? null,
    sceneLayerCount: sceneLayers.length,
    sceneLayers: sceneLayers.map((layer) => layer?.name || layer?._name || layer?.caption || layer?.dataName).filter(Boolean),
    onlineBasemapInstalled: Boolean(viewer?.__onlineBasemap?.installed),
    onlineBasemapStatus: viewer?.__onlineBasemap?.status || "not_configured",
    onlineBasemapSource: viewer?.__onlineBasemap?.source || "",
    onlineRegionalImageryInstalled: Boolean(viewer?.__onlineRegionalTileOverlay?.installed),
    onlineRegionalImageryTiles: viewer?.__onlineRegionalTileOverlay?.tileCount || 0,
    onlineRegionalImageryZoom: viewer?.__onlineRegionalTileOverlay?.zoom || null,
    onlineTerrainInstalled: Boolean(viewer?.__onlineTerrain?.installed),
    onlineTerrainStatus: viewer?.__onlineTerrain?.status || "not_configured",
    onlineTerrainSource: viewer?.__onlineTerrain?.source || "",
  };
}

export function updateCurrentPoint(viewer, SuperMap3D, currentPoint, trails = {}) {
  if (!viewer || !SuperMap3D) return;
  clearDemoEntitiesByPrefix(viewer, CURRENT_POINT_PREFIX, {
    excludeNames: currentPoint ? [CURRENT_UAV_MODEL_NAME] : [],
  });
  if (!currentPoint) {
    viewer.__uavRenderState = null;
  }
  drawFlightTrailComparison(viewer, SuperMap3D, trails.referenceTrail || [], trails.actualTrail || []);
  drawVisualMatchPoints(viewer, SuperMap3D, trails.visualMatchPoints || []);
  drawCurrentPoint(viewer, SuperMap3D, currentPoint, trails.actualTrail || [], trails.referenceTrail || []);
}

export function destroyViewer(viewer) {
  if (!viewer) return;
  try {
    viewer.entities?.removeAll?.();
    viewer.destroy?.();
  } catch (error) {
    console.warn("SuperMap Viewer cleanup failed", error);
  }
}

function clearDemoEntitiesByPrefix(viewer, prefix, options = {}) {
  if (!viewer?.entities) return;
  const excludeNames = new Set(options.excludeNames || []);
  const entities = viewer.entities.values || [];
  [...entities]
    .filter((entity) => entity?.name?.startsWith(prefix) && !excludeNames.has(entity.name))
    .forEach((entity) => viewer.entities.remove(entity));
}

function drawDemoBuildings(viewer, SuperMap3D, task, obstacles) {
  const ring = task?.area?.coordinates?.[0];
  if (!ring?.length) return;
  const lons = ring.map((point) => point[0]);
  const lats = ring.map((point) => point[1]);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);

  const clusters = [
    { lon: 0.23, lat: 0.24, rows: 2, cols: 3, height: 42 },
    { lon: 0.72, lat: 0.30, rows: 2, cols: 4, height: 58 },
    { lon: 0.80, lat: 0.72, rows: 3, cols: 3, height: 46 },
    { lon: 0.42, lat: 0.52, rows: 2, cols: 2, height: 35 },
  ];

  clusters.forEach((cluster, clusterIndex) => {
    for (let row = 0; row < cluster.rows; row += 1) {
      for (let col = 0; col < cluster.cols; col += 1) {
        const lon = lerp(minLon, maxLon, cluster.lon) + (col - (cluster.cols - 1) / 2) * 0.0032;
        const lat = lerp(minLat, maxLat, cluster.lat) + (row - (cluster.rows - 1) / 2) * 0.0027;
        const height = cluster.height + ((row + col + clusterIndex) % 4) * 12;
        addBoxBuilding(viewer, SuperMap3D, `demo-building-${clusterIndex}-${row}-${col}`, [lon, lat], {
          width: 155,
          depth: 118,
          height,
          color: ((row + col) % 2 === 0) ? "LIGHTSLATEGRAY" : "SLATEGRAY",
        });
      }
    }
  });

  obstacles
    .filter((obstacle) => obstacle.type === "building" || obstacle.type === "tower")
    .forEach((obstacle) => {
      if (obstacle.type === "tower") {
        addTower(viewer, SuperMap3D, `demo-building-${obstacle.id}`, obstacle.position, obstacle.height_m || 65);
        return;
      }
      addBoxBuilding(viewer, SuperMap3D, `demo-building-${obstacle.id}`, obstacle.position, {
        width: 180,
        depth: 140,
        height: obstacle.height_m || 52,
        color: "DARKGRAY",
      });
    });
}

function drawRoutes(viewer, SuperMap3D, routes, selectedRoute, replannedRoute) {
  routes.forEach((route) => {
    const color = route.id === selectedRoute?.id ? colorWithAlpha(SuperMap3D, "ORANGE", 0.88) : routeColor(SuperMap3D, route.mode);
    const selected = route.id === selectedRoute?.id;
    addPolyline(viewer, SuperMap3D, `demo-route-${route.id}`, route.points, color, selected ? 5 : 2, {
      minHeight: FLIGHT_PATH_MIN_HEIGHT,
    });
  });
  if (replannedRoute?.route) {
    addPolyline(viewer, SuperMap3D, "demo-route-replanned", replannedRoute.route.points, colorWithAlpha(SuperMap3D, "PURPLE", 0.95), 4, {
      minHeight: FLIGHT_PATH_MIN_HEIGHT + 4,
    });
  }
}

function drawRiskZones(viewer, SuperMap3D, zones) {
  zones.forEach((zone) => {
    const color = zone.level >= 5 ? colorWithAlpha(SuperMap3D, "RED", 0.26) : colorWithAlpha(SuperMap3D, "ORANGE", 0.24);
    const height = zone.level >= 5 ? 76 : 56;
    addPolygon(viewer, SuperMap3D, `demo-risk-${zone.id}`, zone.polygon, color, colorWithAlpha(SuperMap3D, "RED", 0.85), { height, extrudedHeight: height + zone.level * 12 });
    addZoneBeacon(viewer, SuperMap3D, `demo-risk-beacon-${zone.id}`, centroid(zone.polygon), zone.level >= 5 ? "RED" : "ORANGE", height + zone.level * 12);
  });
}

function drawTemporaryRisk(viewer, SuperMap3D, temporaryRisk) {
  if (!temporaryRisk?.risk) return;
  addPolygon(
    viewer,
    SuperMap3D,
    "demo-risk-temporary",
    temporaryRisk.risk.polygon,
    colorWithAlpha(SuperMap3D, "PURPLE", 0.28),
    colorWithAlpha(SuperMap3D, "PURPLE", 0.95),
    { height: 82, extrudedHeight: 162 }
  );
  addZoneBeacon(viewer, SuperMap3D, "demo-risk-temporary-beacon", centroid(temporaryRisk.risk.polygon), "PURPLE", 174);
}

function drawVisionTiles(viewer, SuperMap3D, tiles) {
  tiles.forEach((tile) => {
    addPolygon(
      viewer,
      SuperMap3D,
      `demo-vision-tile-${tile.tile_id}`,
      tile.bbox,
      colorWithAlpha(SuperMap3D, "DODGERBLUE", 0.04),
      colorWithAlpha(SuperMap3D, "DODGERBLUE", 0.22),
      { height: 138 }
    );
  });
}

function drawVisionCandidates(viewer, SuperMap3D, candidates) {
  candidates.forEach((candidate) => {
    const alpha = candidate.status === "best" ? 0.32 : 0.15;
    addPolygon(
      viewer,
      SuperMap3D,
      `demo-vision-candidate-${candidate.tile_id}`,
      candidate.bbox,
      colorWithAlpha(SuperMap3D, "CYAN", alpha),
      colorWithAlpha(SuperMap3D, "CYAN", 0.8),
      { height: 148, extrudedHeight: candidate.status === "best" ? 172 : 158 }
    );
  });
}

function drawVisualMatchPoints(viewer, SuperMap3D, matches) {
  matches.forEach((match, index) => {
    if (!match?.point) return;
    const quality = matchQuality(match.confidence);
    const point = elevateFlightPoint(match.point, FLIGHT_PATH_MIN_HEIGHT + 24);
    const size = Math.min(18, 9 + Math.round((match.matchedPoints || 0) / 18));
    addPoint(
      viewer,
      SuperMap3D,
      `demo-current-uav-visual-match-${match.id || index}`,
      [point[0], point[1], point[2] + 8],
      colorWithAlpha(SuperMap3D, quality.color, 0.94),
      size,
      colorWithAlpha(SuperMap3D, "WHITE", 0.92)
    );
  });
}

function matchQuality(confidence = 0) {
  if (confidence >= 0.75) return { label: "good", color: "LIME" };
  if (confidence >= 0.5) return { label: "warn", color: "YELLOW" };
  return { label: "bad", color: "RED" };
}

function drawTaskPoints(viewer, SuperMap3D, task) {
  if (!task) return;
  addTaskMarker(viewer, SuperMap3D, "demo-start", task.start, {
    label: "起点",
    detail: "任务出发",
    colorName: "LIME",
  });
  addTaskMarker(viewer, SuperMap3D, "demo-target", task.target, {
    label: "终点",
    detail: "目标位置",
    colorName: "RED",
  });
}

function drawCurrentPoint(viewer, SuperMap3D, currentPoint, actualTrail = [], referenceTrail = []) {
  if (!currentPoint) return;
  const targetPoint = elevateFlightPoint(currentPoint, UAV_MODEL_MIN_HEIGHT);
  const headingTrail = referenceTrail?.length >= 2 ? referenceTrail : actualTrail;
  const targetHeading = headingFromTrail(headingTrail, currentPoint);
  const renderState = smoothUavRenderState(viewer, targetPoint, targetHeading);
  const modelPoint = renderState.point;
  const heading = renderState.heading;
  const accentColor = colorWithAlpha(SuperMap3D, "CYAN", 0.62);

  addVerticalLine(viewer, SuperMap3D, "demo-current-uav-altitude", modelPoint, colorWithAlpha(SuperMap3D, "CYAN", 0.44));
  addPoint(viewer, SuperMap3D, "demo-current-uav-shadow", [modelPoint[0], modelPoint[1], UAV_SHADOW_HEIGHT], colorWithAlpha(SuperMap3D, "BLACK", 0.18), 24);
  const modelAdded = addDroneModel(viewer, SuperMap3D, CURRENT_UAV_MODEL_NAME, modelPoint, heading);
  if (!modelAdded) {
    drawFallbackDroneSymbol(viewer, SuperMap3D, modelPoint, heading);
  }
  addPoint(viewer, SuperMap3D, "demo-current-uav-position-ring", modelPoint, colorWithAlpha(SuperMap3D, "CYAN", 0.12), 34, accentColor);
}

function drawFallbackDroneSymbol(viewer, SuperMap3D, modelPoint, heading) {
  const bodyColor = colorWithAlpha(SuperMap3D, "WHITE", 0.96);
  const accentColor = colorWithAlpha(SuperMap3D, "CYAN", 0.86);
  const darkColor = colorWithAlpha(SuperMap3D, "BLACK", 0.82);
  const armPoints = [
    offsetByHeading(modelPoint, heading, 0, -16),
    offsetByHeading(modelPoint, heading, 0, 16),
    offsetByHeading(modelPoint, heading, -16, 0),
    offsetByHeading(modelPoint, heading, 16, 0),
  ];
  const rotorPoints = [
    offsetByHeading(modelPoint, heading, -16, -16),
    offsetByHeading(modelPoint, heading, -16, 16),
    offsetByHeading(modelPoint, heading, 16, -16),
    offsetByHeading(modelPoint, heading, 16, 16),
  ];

  addDroneBody(viewer, SuperMap3D, "demo-current-uav-body", modelPoint, bodyColor, accentColor);
  addPolyline(viewer, SuperMap3D, "demo-current-uav-arm-east-west", [armPoints[0], armPoints[1]], accentColor, 5);
  addPolyline(viewer, SuperMap3D, "demo-current-uav-arm-north-south", [armPoints[2], armPoints[3]], accentColor, 5);
  rotorPoints.forEach((point, index) => {
    addRotorDisc(viewer, SuperMap3D, `demo-current-uav-rotor-disc-${index}`, point, accentColor);
    addPoint(viewer, SuperMap3D, `demo-current-uav-rotor-${index}`, point, colorWithAlpha(SuperMap3D, "CYAN", 0.28), 28, accentColor);
    addPoint(viewer, SuperMap3D, `demo-current-uav-motor-${index}`, point, darkColor, 7, bodyColor);
  });
}

function drawFlightTrailComparison(viewer, SuperMap3D, referenceTrail, actualTrail) {
  if (referenceTrail?.length >= 2) {
    addPolyline(
      viewer,
      SuperMap3D,
      "demo-current-uav-reference-trail",
      referenceTrail,
      colorWithAlpha(SuperMap3D, "WHITE", 0.52),
      3,
      { minHeight: FLIGHT_PATH_MIN_HEIGHT + 2 }
    );
  }
  if (actualTrail?.length >= 2) {
    addPolyline(
      viewer,
      SuperMap3D,
      "demo-current-uav-actual-trail",
      actualTrail,
      colorWithAlpha(SuperMap3D, "ORANGE", 0.9),
      4,
      { minHeight: FLIGHT_PATH_MIN_HEIGHT + 6 }
    );
  }
}

function addBoxBuilding(viewer, SuperMap3D, name, point, options) {
  const height = options.height ?? 42;
  const footprint = rectangleAroundMeters(point, options.width ?? 140, options.depth ?? 120);
  addPolygon(
    viewer,
    SuperMap3D,
    name,
    footprint,
    colorWithAlpha(SuperMap3D, options.color || "SLATEGRAY", 0.78),
    colorWithAlpha(SuperMap3D, "WHITE", 0.35),
    { height: 0, extrudedHeight: height }
  );
}

function addTower(viewer, SuperMap3D, name, point, height) {
  const mastTop = [point[0], point[1], height];
  addVerticalLine(viewer, SuperMap3D, name, mastTop, colorWithAlpha(SuperMap3D, "WHITE", 0.75));
  addPolyline(viewer, SuperMap3D, `${name}-cross-a`, [offsetMeters(mastTop, -14, 0), offsetMeters(mastTop, 14, 0)], colorWithAlpha(SuperMap3D, "ORANGE", 0.75), 3);
  addPolyline(viewer, SuperMap3D, `${name}-cross-b`, [offsetMeters(mastTop, 0, -14), offsetMeters(mastTop, 0, 14)], colorWithAlpha(SuperMap3D, "ORANGE", 0.75), 3);
  addPoint(viewer, SuperMap3D, `${name}-beacon`, [point[0], point[1], height + 8], colorWithAlpha(SuperMap3D, "ORANGE", 0.95), 10, colorWithAlpha(SuperMap3D, "WHITE", 0.9));
}

function addTaskMarker(viewer, SuperMap3D, name, point, options) {
  if (!point) return;
  const color = colorWithAlpha(SuperMap3D, options.colorName, 0.92);
  const softColor = colorWithAlpha(SuperMap3D, options.colorName, 0.16);
  const outlineColor = colorWithAlpha(SuperMap3D, "WHITE", 0.95);
  const topPoint = [point[0], point[1], TASK_MARKER_HEIGHT];

  addGroundRing(viewer, SuperMap3D, `${name}-ground-ring`, [point[0], point[1], TASK_MARKER_RING_HEIGHT], softColor, color);
  addVerticalLine(viewer, SuperMap3D, `${name}-mast`, topPoint, colorWithAlpha(SuperMap3D, options.colorName, 0.78));
  addPoint(viewer, SuperMap3D, `${name}-pin`, topPoint, color, 16, outlineColor);
  addTextLabel(viewer, SuperMap3D, `${name}-label`, [point[0], point[1], TASK_MARKER_HEIGHT + 22], {
    text: `${options.label}\n${options.detail}`,
    fillColor: colorWithAlpha(SuperMap3D, "WHITE", 1),
    outlineColor: colorWithAlpha(SuperMap3D, "BLACK", 0.72),
    backgroundColor: colorWithAlpha(SuperMap3D, "BLACK", 0.72),
    font: "600 15px Microsoft YaHei, sans-serif",
    pixelOffsetY: -16,
  });
}

function addDroneModel(viewer, SuperMap3D, name, point, headingDeg) {
  try {
    const position = SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2]);
    const orientation = droneOrientation(SuperMap3D, position, headingDeg);
    const existing = findEntityByName(viewer, name);
    if (existing) {
      existing.position = position;
      if (orientation) {
        existing.orientation = orientation;
      }
      existing.show = true;
      return true;
    }
    const entity = {
      id: name,
      name,
      properties: { supermapDemo: true },
      position,
      model: {
        uri: UAV_MODEL_URL,
        scale: UAV_MODEL_SCALE,
        minimumPixelSize: UAV_MODEL_MIN_PIXEL_SIZE,
        maximumScale: UAV_MODEL_MAXIMUM_SCALE,
        runAnimations: true,
        silhouetteColor: colorWithAlpha(SuperMap3D, "WHITE", 0.72),
        silhouetteSize: 0.8,
      },
    };
    if (orientation) {
      entity.orientation = orientation;
    }
    viewer.entities.add(entity);
    return true;
  } catch (error) {
    console.warn(`Failed to add drone model: ${name}`, error);
    return false;
  }
}

function findEntityByName(viewer, name) {
  return viewer?.entities?.getById?.(name) || (viewer?.entities?.values || []).find((entity) => entity?.name === name) || null;
}

function smoothUavRenderState(viewer, targetPoint, targetHeading) {
  const previous = viewer.__uavRenderState;
  if (!previous || geographicDistanceMeters(previous.point, targetPoint) > UAV_RENDER_SNAP_DISTANCE) {
    viewer.__uavRenderState = {
      point: targetPoint,
      heading: normalizeDegrees(targetHeading),
    };
    return viewer.__uavRenderState;
  }

  const point = [
    lerp(previous.point[0], targetPoint[0], UAV_POSITION_SMOOTHING),
    lerp(previous.point[1], targetPoint[1], UAV_POSITION_SMOOTHING),
    lerp(previous.point[2], targetPoint[2], UAV_POSITION_SMOOTHING),
  ];
  const headingDelta = shortestAngleDelta(previous.heading, targetHeading);
  const heading = Math.abs(headingDelta) < UAV_HEADING_DEADBAND_DEG
    ? previous.heading
    : normalizeDegrees(previous.heading + headingDelta * UAV_HEADING_SMOOTHING);
  viewer.__uavRenderState = { point, heading };
  return viewer.__uavRenderState;
}

function droneOrientation(SuperMap3D, position, headingDeg) {
  try {
    if (!SuperMap3D.Transforms?.headingPitchRollQuaternion || !SuperMap3D.HeadingPitchRoll) {
      return null;
    }
    const heading = (headingDeg * Math.PI) / 180 + UAV_MODEL_HEADING_OFFSET;
    return SuperMap3D.Transforms.headingPitchRollQuaternion(
      position,
      new SuperMap3D.HeadingPitchRoll(heading, 0, 0)
    );
  } catch (error) {
    console.warn("Failed to calculate drone orientation", error);
    return null;
  }
}

function addDroneBody(viewer, SuperMap3D, name, point, material, outlineColor) {
  try {
    viewer.entities.add({
      name,
      properties: { supermapDemo: true },
      position: SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2]),
      ellipsoid: {
        radii: new SuperMap3D.Cartesian3(8, 5, 2.6),
        material,
        outline: true,
        outlineColor,
      },
    });
  } catch (error) {
    console.warn(`Failed to add drone body: ${name}`, error);
    addPoint(viewer, SuperMap3D, name, point, material, 15, outlineColor);
  }
}

function addRotorDisc(viewer, SuperMap3D, name, point, material) {
  try {
    viewer.entities.add({
      name,
      properties: { supermapDemo: true },
      position: SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2] + 0.8),
      ellipse: {
        semiMajorAxis: 7,
        semiMinorAxis: 7,
        material: colorWithAlpha(SuperMap3D, "CYAN", 0.16),
        outline: true,
        outlineColor: material,
        height: point[2] + 0.8,
      },
    });
  } catch (error) {
    console.warn(`Failed to add drone rotor disc: ${name}`, error);
  }
}

function drawLuojiaBuildings(viewer, SuperMap3D, buildings, terrain = null) {
  buildings.forEach((building) => {
    const height = Math.max(8, Math.min(Number(building.height_m) || 18, 90));
    const ground = sampleTerrainHeight(terrain, centroid(building.polygon)) ?? 8;
    addPolygon(
      viewer,
      SuperMap3D,
      `demo-luojia-building-${building.id}`,
      building.polygon,
      colorWithAlpha(SuperMap3D, height > 35 ? "LIGHTSLATEGRAY" : "DARKGRAY", 0.58),
      colorWithAlpha(SuperMap3D, "WHITE", 0.28),
      {
        height: ground + 1.5,
        extrudedHeight: ground + height,
      }
    );
  });
}

function sampleTerrainHeight(terrain, point) {
  if (!terrain?.vertices?.length || !point) return null;
  let best = null;
  let bestDistance = Number.POSITIVE_INFINITY;
  terrain.vertices.forEach((vertex) => {
    const dx = vertex.lon - point[0];
    const dy = vertex.lat - point[1];
    const distance = dx * dx + dy * dy;
    if (distance < bestDistance) {
      bestDistance = distance;
      best = vertex.height_m;
    }
  });
  return Number.isFinite(best) ? best : null;
}

function addPolyline(viewer, SuperMap3D, name, points, material, width = 3, options = {}) {
  if (!points?.length) return;
  try {
    viewer.entities.add({
      name,
      properties: { supermapDemo: true },
      polyline: {
        positions: points.map((point) => {
          const renderPoint = options.minHeight ? elevateFlightPoint(point, options.minHeight) : point;
          return SuperMap3D.Cartesian3.fromDegrees(renderPoint[0], renderPoint[1], renderPoint[2] || 120);
        }),
        width,
        material,
        depthFailMaterial: material,
        clampToGround: false,
      },
    });
  } catch (error) {
    console.warn(`Failed to add demo polyline: ${name}`, error);
  }
}

function addPolygon(viewer, SuperMap3D, name, points, material, outlineColor, options = {}) {
  if (!points?.length) return;
  const height = options.height ?? 60;
  const positions = points.map((point) => SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2] || height));
  try {
    viewer.entities.add({
      name,
      properties: { supermapDemo: true },
      polygon: {
        hierarchy: SuperMap3D.PolygonHierarchy ? new SuperMap3D.PolygonHierarchy(positions) : positions,
        material,
        outline: true,
        outlineColor,
        height,
        extrudedHeight: options.extrudedHeight,
      },
    });
  } catch (error) {
    console.warn(`Failed to add demo polygon: ${name}`, error);
  }
}

function addPoint(viewer, SuperMap3D, name, point, color, pixelSize, outlineColor = undefined) {
  try {
    viewer.entities.add({
      name,
      properties: { supermapDemo: true },
      position: SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2] || 120),
      point: {
        pixelSize,
        color,
        outlineColor,
        outlineWidth: outlineColor ? 2 : 0,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    });
  } catch (error) {
    console.warn(`Failed to add demo point: ${name}`, error);
  }
}

function addGroundRing(viewer, SuperMap3D, name, point, material, outlineColor) {
  try {
    viewer.entities.add({
      name,
      properties: { supermapDemo: true },
      position: SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2] || TASK_MARKER_RING_HEIGHT),
      ellipse: {
        semiMajorAxis: 30,
        semiMinorAxis: 30,
        material,
        outline: true,
        outlineColor,
        height: point[2] || TASK_MARKER_RING_HEIGHT,
      },
    });
  } catch (error) {
    console.warn(`Failed to add ground ring: ${name}`, error);
  }
}

function addTextLabel(viewer, SuperMap3D, name, point, options) {
  try {
    viewer.entities.add({
      name,
      properties: { supermapDemo: true },
      position: SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2] || TASK_MARKER_HEIGHT),
      point: options.markerColor
        ? {
            pixelSize: 8,
            color: options.markerColor,
            outlineColor: colorWithAlpha(SuperMap3D, "WHITE", 0.95),
            outlineWidth: 2,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          }
        : undefined,
      label: {
        text: options.text,
        font: options.font || "500 13px Microsoft YaHei, sans-serif",
        fillColor: options.fillColor || colorWithAlpha(SuperMap3D, "WHITE", 1),
        outlineColor: options.outlineColor || colorWithAlpha(SuperMap3D, "BLACK", 0.72),
        outlineWidth: 3,
        style: SuperMap3D.LabelStyle?.FILL_AND_OUTLINE,
        showBackground: true,
        backgroundColor: options.backgroundColor || colorWithAlpha(SuperMap3D, "BLACK", 0.62),
        backgroundPadding: SuperMap3D.Cartesian2 ? new SuperMap3D.Cartesian2(9, 6) : undefined,
        pixelOffset: SuperMap3D.Cartesian2 ? new SuperMap3D.Cartesian2(0, options.pixelOffsetY || -10) : undefined,
        verticalOrigin: SuperMap3D.VerticalOrigin?.BOTTOM,
        horizontalOrigin: SuperMap3D.HorizontalOrigin?.CENTER,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    });
  } catch (error) {
    console.warn(`Failed to add text label: ${name}`, error);
  }
}

function addVerticalLine(viewer, SuperMap3D, name, point, material) {
  const baseHeight = UAV_SHADOW_HEIGHT;
  const topHeight = point[2] || 120;
  viewer.entities.add({
    name,
    properties: { supermapDemo: true },
    polyline: {
      positions: [
        SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], baseHeight),
        SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], topHeight),
      ],
      width: 2,
      material,
      depthFailMaterial: material,
    },
  });
}

function addZoneBeacon(viewer, SuperMap3D, name, point, colorName, height) {
  if (!point) return;
  const color = colorWithAlpha(SuperMap3D, colorName, 0.68);
  viewer.entities.add({
    name,
    properties: { supermapDemo: true },
    position: SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], height),
    point: {
      pixelSize: 9,
      color,
      outlineColor: colorWithAlpha(SuperMap3D, "WHITE", 0.9),
      outlineWidth: 2,
    },
  });
}

function centroid(points) {
  if (!points?.length) return null;
  const usable = points.slice(0, points.length > 1 ? -1 : points.length);
  const totals = usable.reduce(
    (acc, point) => {
      acc.lon += point[0];
      acc.lat += point[1];
      return acc;
    },
    { lon: 0, lat: 0 }
  );
  return [totals.lon / usable.length, totals.lat / usable.length];
}

function offsetMeters(point, eastMeters, northMeters) {
  const latRad = (point[1] * Math.PI) / 180;
  const metersPerDegreeLat = 111320;
  const metersPerDegreeLon = Math.max(1, 111320 * Math.cos(latRad));
  return [
    point[0] + eastMeters / metersPerDegreeLon,
    point[1] + northMeters / metersPerDegreeLat,
    point[2] || 120,
  ];
}

function elevateFlightPoint(point, minHeight = FLIGHT_PATH_MIN_HEIGHT) {
  if (!point) return point;
  const height = Math.max(Number(point[2]) || 120, minHeight);
  return [point[0], point[1], height];
}

function headingFromTrail(trail = [], fallbackPoint = null) {
  const points = [...trail, fallbackPoint].filter(Boolean);
  if (points.length < 2) return 45;
  const current = points[points.length - 1];
  const previous = [...points].reverse().find((point) => {
    return Math.abs(point[0] - current[0]) > 0.000001 || Math.abs(point[1] - current[1]) > 0.000001;
  });
  if (!previous) return 45;
  const lonMeters = (current[0] - previous[0]) * 111320 * Math.cos((current[1] * Math.PI) / 180);
  const latMeters = (current[1] - previous[1]) * 111320;
  return ((Math.atan2(lonMeters, latMeters) * 180) / Math.PI + 360) % 360;
}

function offsetByHeading(point, headingDeg, forwardMeters, rightMeters) {
  const heading = (headingDeg * Math.PI) / 180;
  const east = Math.sin(heading) * forwardMeters + Math.cos(heading) * rightMeters;
  const north = Math.cos(heading) * forwardMeters - Math.sin(heading) * rightMeters;
  return offsetMeters(point, east, north);
}

function geographicDistanceMeters(pointA, pointB) {
  if (!pointA || !pointB) return Number.POSITIVE_INFINITY;
  const avgLat = (((pointA[1] || 0) + (pointB[1] || 0)) / 2) * (Math.PI / 180);
  const east = ((pointB[0] || 0) - (pointA[0] || 0)) * 111320 * Math.cos(avgLat);
  const north = ((pointB[1] || 0) - (pointA[1] || 0)) * 111320;
  const up = (pointB[2] || 0) - (pointA[2] || 0);
  return Math.hypot(east, north, up);
}

function shortestAngleDelta(fromDeg, toDeg) {
  return ((normalizeDegrees(toDeg) - normalizeDegrees(fromDeg) + 540) % 360) - 180;
}

function normalizeDegrees(degrees) {
  return ((degrees % 360) + 360) % 360;
}

function rectangleAroundMeters(point, widthMeters, depthMeters) {
  const westSouth = offsetMeters(point, -widthMeters / 2, -depthMeters / 2);
  const eastSouth = offsetMeters(point, widthMeters / 2, -depthMeters / 2);
  const eastNorth = offsetMeters(point, widthMeters / 2, depthMeters / 2);
  const westNorth = offsetMeters(point, -widthMeters / 2, depthMeters / 2);
  return [
    [westSouth[0], westSouth[1]],
    [eastSouth[0], eastSouth[1]],
    [eastNorth[0], eastNorth[1]],
    [westNorth[0], westNorth[1]],
    [westSouth[0], westSouth[1]],
  ];
}

function lerp(start, end, ratio) {
  return start + (end - start) * ratio;
}

function lonLatToWebMercatorTile(lon, lat, zoom) {
  const clampedLat = Math.max(-85.05112878, Math.min(85.05112878, lat));
  const scale = 2 ** zoom;
  const x = Math.floor(((lon + 180) / 360) * scale);
  const latRad = (clampedLat * Math.PI) / 180;
  const y = Math.floor(
    ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * scale,
  );
  return {
    x: clampTileIndex(x, zoom),
    y: clampTileIndex(y, zoom),
  };
}

function webMercatorTileBounds(x, y, zoom) {
  const scale = 2 ** zoom;
  const west = (x / scale) * 360 - 180;
  const east = ((x + 1) / scale) * 360 - 180;
  const north = webMercatorTileYToLat(y, zoom);
  const south = webMercatorTileYToLat(y + 1, zoom);
  return { west, south, east, north };
}

function webMercatorTileYToLat(y, zoom) {
  const n = Math.PI - (2 * Math.PI * y) / 2 ** zoom;
  return (180 / Math.PI) * Math.atan(Math.sinh(n));
}

function clampTileIndex(value, zoom) {
  const max = 2 ** zoom - 1;
  return Math.max(0, Math.min(max, value));
}

export function fitToTask(viewer, SuperMap3D, task, supermapConfig = null) {
  const ring = task?.area?.coordinates?.[0];
  if (!ring?.length || !viewer.camera || !SuperMap3D.Cartesian3) return;
  const lons = ring.map((point) => point[0]);
  const lats = ring.map((point) => point[1]);
  const centerLon = (Math.min(...lons) + Math.max(...lons)) / 2;
  const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
  const spanLon = Math.max(0.001, Math.max(...lons) - Math.min(...lons));
  const spanLat = Math.max(0.001, Math.max(...lats) - Math.min(...lats));
  const lonMeters = spanLon * 111320 * Math.max(0.2, Math.cos((centerLat * Math.PI) / 180));
  const latMeters = spanLat * 111320;
  const isLuojia = isLuojiaScene(supermapConfig);
  const altitude = isLuojia ? 1900 : clamp(Math.max(lonMeters, latMeters) * 2.1, 1800, 9000);
  const offsetLon = isLuojia ? spanLon * 0.65 : spanLon * 0.55;
  const offsetLat = isLuojia ? spanLat * 1.05 : spanLat * 0.75;
  const destination = SuperMap3D.Cartesian3.fromDegrees(centerLon - offsetLon, centerLat - offsetLat, altitude);
  const orientation = {
    heading: SuperMap3D.Math?.toRadians ? SuperMap3D.Math.toRadians(32) : 0.56,
    pitch: SuperMap3D.Math?.toRadians ? SuperMap3D.Math.toRadians(-57) : -0.99,
    roll: 0,
  };
  if (viewer.camera.flyTo) {
    viewer.camera.flyTo({ destination, orientation, duration: 0.75 });
    return;
  }
  viewer.camera.setView({ destination, orientation });
}

export function fitToLargeArea(viewer, SuperMap3D, supermapConfig = null) {
  if (!viewer?.camera || !SuperMap3D.Cartesian3) return;
  const view = supermapConfig?.presentation?.regional_3d_view || supermapConfig?.presentation?.large_area_view || {};
  const destination = SuperMap3D.Cartesian3.fromDegrees(
    view.lon ?? 114.365,
    view.lat ?? 30.54,
    view.altitude_m ?? 9200
  );
  const orientation = {
    heading: SuperMap3D.Math?.toRadians ? SuperMap3D.Math.toRadians(view.heading_deg ?? 18) : 0.31,
    pitch: SuperMap3D.Math?.toRadians ? SuperMap3D.Math.toRadians(view.pitch_deg ?? -56) : -0.98,
    roll: 0,
  };
  if (viewer.camera.flyTo) {
    viewer.camera.flyTo({ destination, orientation, duration: 1.2 });
    return;
  }
  viewer.camera.setView({ destination, orientation });
}

function buildLayerVisibility(layers) {
  const visibility = {
    terrain: true,
    imagery: true,
    risk_zone: true,
    obstacle: true,
  };
  layers.forEach((layer) => {
    if (layer?.id && Object.prototype.hasOwnProperty.call(visibility, layer.id)) {
      visibility[layer.id] = layer.visible !== false;
    }
  });
  return visibility;
}

function hasRealSuperMapScene(data) {
  return Boolean(data?.sceneUrl || data?.supermapConfig?.services?.scene?.url);
}

function shouldUseStaticOrthoInstead(viewer, supermapConfig, names) {
  if (!viewer.__luojiaStaticOrthoEntity || !isLuojiaScene(supermapConfig)) return false;
  return names.filter(Boolean).some((name) => String(name).toLowerCase().includes("luojia_ortho"));
}

function collectSceneLayers(scene) {
  const candidates = [
    scene.layers,
    scene.layers?._layers,
    scene.layers?.layerQueue,
    scene.layers?.values,
    scene.terrainLayers,
    scene.imageryLayers,
  ];
  const layers = [];

  candidates.forEach((candidate) => {
    if (!candidate) return;
    if (Array.isArray(candidate)) {
      layers.push(...candidate);
      return;
    }
    const length = Number(candidate.length);
    if (Number.isFinite(length)) {
      for (let index = 0; index < length; index += 1) {
        const layer = candidate.get?.(index) || candidate.getLayer?.(index) || candidate[index];
        if (layer) layers.push(layer);
      }
    }
  });

  return [...new Set(layers)];
}

function scheduleLayerVisibilityRetry(viewer, layers, supermapConfig) {
  if (!isLuojiaScene(supermapConfig) || viewer.__luojiaLayerRetryScheduled) return;
  viewer.__luojiaLayerRetryPass = viewer.__luojiaLayerRetryPass || 0;
  if (viewer.__luojiaLayerRetryPass >= 4) return;
  viewer.__luojiaLayerRetryScheduled = true;
  const delays = [350, 900, 1800, 3200];
  const delay = delays[viewer.__luojiaLayerRetryPass] || 3200;
  viewer.__luojiaLayerRetryPass += 1;
  window.setTimeout(() => {
    viewer.__luojiaLayerRetryScheduled = false;
    syncSceneLayerVisibility(viewer, layers, supermapConfig);
  }, delay);
}

function layerMatchesAnyName(layer, names) {
  const layerNames = [
    layer?.name,
    layer?._name,
    layer?.layerName,
    layer?.datasetName,
    layer?.imageryProvider?.name,
  ]
    .filter(Boolean)
    .map((value) => String(value).toLowerCase());
  const needles = names.filter(Boolean).map((value) => String(value).toLowerCase());
  return layerNames.some((layerName) => needles.some((needle) => layerName.includes(needle) || needle.includes(layerName)));
}

function setLayerVisible(layer, visible) {
  try {
    if (typeof layer.setVisible === "function") {
      layer.setVisible(visible);
      return;
    }
    if ("visible" in layer) layer.visible = visible;
    if ("show" in layer) layer.show = visible;
  } catch (error) {
    console.warn("Failed to update SuperMap scene layer visibility", layer?.name || layer, error);
  }
}

function isLuojiaScene(supermapConfig) {
  const text = JSON.stringify({
    scene: supermapConfig?.services?.scene,
    map: supermapConfig?.services?.map,
    workspace: supermapConfig?.iserver?.workspace_path,
  }).toLowerCase();
  return text.includes("luojia");
}

function prepareLuojiaViewer(viewer, SuperMap3D) {
  try {
    if (viewer.scene?.globe) {
      viewer.scene.globe.depthTestAgainstTerrain = false;
      if (SuperMap3D?.Color?.BLACK?.withAlpha) {
        viewer.scene.globe.baseColor = SuperMap3D.Color.BLACK.withAlpha(0.02);
      }
    }
    if (viewer.scene) {
      viewer.scene.highDynamicRange = false;
      viewer.scene.requestRenderMode = false;
    }
  } catch (error) {
    console.warn("Failed to prepare Luojia viewer fallback rendering", error);
  }
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function installGentleWheelZoom(container, viewer) {
  if (!container || !viewer?.camera) return () => {};

  const controller = viewer.scene?.screenSpaceCameraController;
  const previousEnableZoom = controller?.enableZoom;
  if (controller) {
    controller.enableZoom = false;
  }

  const onWheel = (event) => {
    if (!viewer.camera) return;
    event.preventDefault();
    event.stopPropagation();

    const height = viewer.camera.positionCartographic?.height || 1200;
    const wheelUnits = Math.min(Math.abs(event.deltaY) / 120, 4);
    const amount = Math.max(8, Math.min(height * 0.045 * wheelUnits, 420));

    if (event.deltaY > 0) {
      viewer.camera.zoomOut?.(amount);
    } else {
      viewer.camera.zoomIn?.(amount);
    }
  };

  container.addEventListener("wheel", onWheel, { passive: false, capture: true });

  return () => {
    container.removeEventListener("wheel", onWheel, { capture: true });
    if (controller && previousEnableZoom !== undefined) {
      controller.enableZoom = previousEnableZoom;
    }
  };
}

async function getScene(viewer) {
  if (viewer.scenePromise?.then) return viewer.scenePromise;
  return viewer.scene;
}

function routeColor(SuperMap3D, mode) {
  if (mode === "safest") return colorWithAlpha(SuperMap3D, "LIME", 0.9);
  if (mode === "shortest") return colorWithAlpha(SuperMap3D, "DODGERBLUE", 0.9);
  return colorWithAlpha(SuperMap3D, "ORANGERED", 0.9);
}

function colorWithAlpha(SuperMap3D, name, alpha) {
  const color = SuperMap3D.Color?.[name] || SuperMap3D.Color?.WHITE;
  return color?.withAlpha ? color.withAlpha(alpha) : color;
}

function createImageMaterial(SuperMap3D, imageUrl, alpha = 1) {
  if (SuperMap3D.ImageMaterialProperty) {
    return new SuperMap3D.ImageMaterialProperty({
      image: imageUrl,
      transparent: alpha < 1,
      color: colorWithAlpha(SuperMap3D, "WHITE", alpha),
    });
  }
  return imageUrl;
}

function normalizeBase(value) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function loadScript(src) {
  const existing = document.querySelector(`script[data-supermap3d-sdk="${src}"]`);
  if (existing) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.dataset.supermap3dSdk = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`failed to load ${src}`));
    document.head.appendChild(script);
  });
}

function loadCss(href) {
  const existing = document.querySelector(`link[data-supermap3d-css="${href}"]`);
  if (existing) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.dataset.supermap3dCss = href;
    link.onload = () => resolve();
    link.onerror = () => reject(new Error(`failed to load ${href}`));
    document.head.appendChild(link);
  });
}
