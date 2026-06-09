const DEFAULT_SDK_BASE = "/vendor/supermap3d/Build/SuperMap3D";

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
  return new SuperMap3D.Viewer(container, {
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
        alpha: false,
        antialias: true,
        preserveDrawingBuffer: true,
        failIfMajorPerformanceCaveat: false,
      },
    },
  });
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
    .filter((entity) => entity?.properties?.supermapDemo === true || entity?.name?.startsWith("demo-"))
    .forEach((entity) => viewer.entities.remove(entity));
}

export function drawDemoOverlay(viewer, SuperMap3D, data) {
  if (!viewer || !SuperMap3D) return;
  clearDemoEntities(viewer);
  drawRiskZones(viewer, SuperMap3D, data.taskDetail?.risk_zones || []);
  drawTemporaryRisk(viewer, SuperMap3D, data.temporaryRisk);
  drawVisionTiles(viewer, SuperMap3D, data.visionTiles || []);
  drawVisionCandidates(viewer, SuperMap3D, data.visionResult?.candidates || []);
  drawRoutes(viewer, SuperMap3D, data.routes || [], data.selectedRoute, data.replannedRoute);
  drawTaskPoints(viewer, SuperMap3D, data.selectedTask);
  drawCurrentPoint(viewer, SuperMap3D, data.currentPoint);
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

function drawRoutes(viewer, SuperMap3D, routes, selectedRoute, replannedRoute) {
  routes.forEach((route) => {
    const color = route.id === selectedRoute?.id ? colorWithAlpha(SuperMap3D, "ORANGERED", 0.95) : routeColor(SuperMap3D, route.mode);
    const selected = route.id === selectedRoute?.id;
    if (selected) {
      addPolyline(viewer, SuperMap3D, `demo-route-${route.id}-halo`, route.points, colorWithAlpha(SuperMap3D, "WHITE", 0.42), 9);
    }
    addPolyline(viewer, SuperMap3D, `demo-route-${route.id}`, route.points, color, selected ? 4 : 2);
  });
  if (replannedRoute?.route) {
    addPolyline(viewer, SuperMap3D, "demo-route-replanned-halo", replannedRoute.route.points, colorWithAlpha(SuperMap3D, "WHITE", 0.36), 10);
    addPolyline(viewer, SuperMap3D, "demo-route-replanned", replannedRoute.route.points, colorWithAlpha(SuperMap3D, "PURPLE", 0.95), 4);
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
    addPolygon(viewer, SuperMap3D, `demo-vision-tile-${tile.tile_id}`, tile.bbox, colorWithAlpha(SuperMap3D, "STEELBLUE", 0.06), colorWithAlpha(SuperMap3D, "STEELBLUE", 0.28));
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
      { height: 96, extrudedHeight: candidate.status === "best" ? 132 : 110 }
    );
  });
}

function drawTaskPoints(viewer, SuperMap3D, task) {
  if (!task) return;
  addPoint(viewer, SuperMap3D, "demo-start", task.start, colorWithAlpha(SuperMap3D, "LIME", 1), 12);
  addPoint(viewer, SuperMap3D, "demo-target", task.target, colorWithAlpha(SuperMap3D, "RED", 1), 12);
}

function drawCurrentPoint(viewer, SuperMap3D, currentPoint) {
  if (!currentPoint) return;
  addPoint(viewer, SuperMap3D, "demo-current-uav", currentPoint, colorWithAlpha(SuperMap3D, "WHITE", 1), 10, colorWithAlpha(SuperMap3D, "BLACK", 1));
  addPoint(viewer, SuperMap3D, "demo-current-uav-ring", currentPoint, colorWithAlpha(SuperMap3D, "CYAN", 0.35), 24, colorWithAlpha(SuperMap3D, "CYAN", 0.9));
  addVerticalLine(viewer, SuperMap3D, "demo-current-uav-altitude", currentPoint, colorWithAlpha(SuperMap3D, "CYAN", 0.72));
}

function addPolyline(viewer, SuperMap3D, name, points, material, width = 3) {
  if (!points?.length) return;
  viewer.entities.add({
    name,
    properties: { supermapDemo: true },
    polyline: {
      positions: points.map((point) => SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2] || 120)),
      width,
      material,
      clampToGround: false,
    },
  });
}

function addPolygon(viewer, SuperMap3D, name, points, material, outlineColor, options = {}) {
  if (!points?.length) return;
  const height = options.height ?? 60;
  const positions = points.map((point) => SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2] || height));
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
}

function addPoint(viewer, SuperMap3D, name, point, color, pixelSize, outlineColor = undefined) {
  viewer.entities.add({
    name,
    properties: { supermapDemo: true },
    position: SuperMap3D.Cartesian3.fromDegrees(point[0], point[1], point[2] || 120),
    point: {
      pixelSize,
      color,
      outlineColor,
      outlineWidth: outlineColor ? 2 : 0,
    },
  });
}

function addVerticalLine(viewer, SuperMap3D, name, point, material) {
  const baseHeight = 50;
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

export function fitToTask(viewer, SuperMap3D, task) {
  const ring = task?.area?.coordinates?.[0];
  if (!ring?.length || !viewer.camera || !SuperMap3D.Rectangle) return;
  const lons = ring.map((point) => point[0]);
  const lats = ring.map((point) => point[1]);
  const rectangle = SuperMap3D.Rectangle.fromDegrees(Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats));
  viewer.camera.setView({ destination: rectangle });
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
