const API_BASE = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${options.method || "GET"} ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

export function fetchOrg() {
  return request("/org");
}

export function kickoffProject(project) {
  return request("/kickoff", {
    method: "POST",
    body: JSON.stringify({ project }),
  });
}

export function fetchAuditLog() {
  return request("/audit-log");
}

export { API_BASE };
