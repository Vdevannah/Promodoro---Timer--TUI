const BASE_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ? JSON.stringify(body.detail) : `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const getState = () => request("/api/state");

export const createTask = (title, estimatePomodoros) =>
  request("/api/tasks", {
    method: "POST",
    body: JSON.stringify({ title, estimate_pomodoros: estimatePomodoros }),
  });

export const createTaskFromTemplate = (templateId, estimatePomodoros) =>
  request(`/api/tasks/from-template/${templateId}`, {
    method: "POST",
    body: JSON.stringify(
      estimatePomodoros ? { estimate_pomodoros: estimatePomodoros } : {}
    ),
  });

export const selectTask = (taskId) =>
  request(`/api/tasks/${taskId}/select`, { method: "POST" });

export const completeTask = (taskId) =>
  request(`/api/tasks/${taskId}/done`, { method: "POST" });

export const removeTask = (taskId) =>
  request(`/api/tasks/${taskId}`, { method: "DELETE" });

export const getTemplates = () => request("/api/templates");

export const createTemplate = (title, estimatePomodoros) =>
  request("/api/templates", {
    method: "POST",
    body: JSON.stringify({ title, estimate_pomodoros: estimatePomodoros }),
  });

export const removeTemplate = (templateId) =>
  request(`/api/templates/${templateId}`, { method: "DELETE" });

export const getSettings = () => request("/api/settings");

export const updateSettings = (patch) =>
  request("/api/settings", { method: "PATCH", body: JSON.stringify(patch) });

export const startTimer = () => request("/api/timer/start", { method: "POST" });
export const pauseTimer = () => request("/api/timer/pause", { method: "POST" });
export const resetTimer = () => request("/api/timer/reset", { method: "POST" });
export const getEta = () => request("/api/timer/eta");

export const getReport = (granularity) => request(`/api/reports?granularity=${granularity}`);
