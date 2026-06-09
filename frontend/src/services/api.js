const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.message || `HTTP ${response.status}`);
  }
  if (!payload.success) {
    throw new Error(payload.message || "request failed");
  }
  return payload.data;
}

export const api = {
  health: () => request("/health"),
  tasks: () => request("/tasks"),
  taskDetail: (taskId) => request(`/tasks/${taskId}`),
  riskZones: (taskId) => request(`/tasks/${encodeURIComponent(taskId)}/risk-zones`),
  updateRiskZones: (taskId, riskZones) =>
    request(`/tasks/${encodeURIComponent(taskId)}/risk-zones`, {
      method: "PUT",
      body: JSON.stringify({ risk_zones: riskZones }),
    }),
  layers: () => request("/layers"),
  supermapConfig: () => request("/supermap/config"),
  supermapServices: () => request("/supermap/services"),
  supermapStatus: () => request("/supermap/status"),
  planRoutes: (body) =>
    request("/routes/plan", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  analyzeRisk: (body) =>
    request("/risks/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  startSimulation: (body) =>
    request("/simulations/start", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  startNavigation: (body) =>
    request("/navigation/start", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  navigationState: (sessionId, timeS) =>
    request(`/navigation/state?session_id=${encodeURIComponent(sessionId)}&time_s=${encodeURIComponent(timeS)}`),
  navigationTimeline: (sessionId) => request(`/navigation/timeline?session_id=${encodeURIComponent(sessionId)}`),
  navigationReplan: (body) =>
    request("/navigation/replan", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  temporaryRisk: (simulationId, body) =>
    request(`/simulations/${simulationId}/temporary-risk`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  replan: (body) =>
    request("/routes/replan", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  visionImages: (taskId) => request(`/vision/images?task_id=${encodeURIComponent(taskId)}`),
  visionTiles: (taskId) => request(`/vision/tiles?task_id=${encodeURIComponent(taskId)}`),
  visionMatch: (body) =>
    request("/vision/match", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  visionSyntheticViews: (body) =>
    request("/vision/synthetic-views", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  visionLocalize: (body) =>
    request("/vision/localize", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  visionLocalizationDetail: (taskId, imageId) =>
    request(`/vision/localizations/${encodeURIComponent(imageId)}?task_id=${encodeURIComponent(taskId)}`),
  visionMatchDetail: (matchId) => request(`/vision/matches/${encodeURIComponent(matchId)}`),
  report: (taskId) => request(`/reports/${taskId}`),
};
