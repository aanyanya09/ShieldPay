
const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 12000);

async function request(path, { method = "GET", body, adminPassword } = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const headers = {};

    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (adminPassword) headers["X-Admin-Password"] = adminPassword;

    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await response.json()
      : { detail: await response.text() };

    if (!response.ok) {
      const detail = data.detail || data.message || `Request failed (${response.status})`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }

    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The request timed out. Please try again.");
    }

    if (error instanceof TypeError) {
      throw new Error("Cannot reach the ShieldPay backend. Check that it is running.");
    }

    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export const api = {
  health: () => request("/api/health"),
  products: async () => {
    const data = await request("/api/products");
    return Array.isArray(data.products) ? data.products : [];
  },
  createOrder: payload => request("/api/orders", { method: "POST", body: payload }),
  assess: payload => request("/api/assess", { method: "POST", body: payload }),
  capture: payload => request("/api/capture", { method: "POST", body: payload }),
  report: payload => request("/api/reports", { method: "POST", body: payload }),
  feedback: payload => request("/api/feedback", { method: "POST", body: payload }),
  adminReports: password => request("/api/admin/reports", { adminPassword: password }),
  adminUpdateReport: (password, payload) =>
    request("/api/admin/reports", {
      method: "POST",
      adminPassword: password,
      body: payload,
    }),
};
