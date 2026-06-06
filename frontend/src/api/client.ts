import type { AppConfig, DeliveryResult, Paper, Report } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const requestOptions = Object.assign({}, options, {
    headers: Object.assign({ "Content-Type": "application/json" }, options?.headers ?? {})
  });
  const response = await fetch(`${API_BASE}${path}`, requestOptions);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  getConfig: () => request<AppConfig>("/api/config"),
  saveConfig: (config: AppConfig) =>
    request<AppConfig>("/api/config", { method: "PUT", body: JSON.stringify(config) }),
  searchPapers: () => request<{ count: number; papers: Paper[]; warnings: string[] }>("/api/papers/search", { method: "POST" }),
  listPapers: () => request<Paper[]>("/api/papers"),
  generateReport: () => request<Report>("/api/reports/generate", { method: "POST" }),
  generateAndSend: () => request<DeliveryResult>("/api/reports/generate-and-send", { method: "POST" }),
  listReports: () => request<Report[]>("/api/reports"),
  sendReport: (reportId: number) => request<DeliveryResult>(`/api/reports/${reportId}/send`, { method: "POST" }),
  sendFeishuTest: () => request<DeliveryResult>("/api/delivery/feishu/test", { method: "POST" })
};
