import { apiClient } from "./client";
import type { ResearchSession, SessionDetail } from "./types";

export async function createSession(): Promise<ResearchSession> {
  const { data } = await apiClient.post<ResearchSession>("/api/sessions");
  return data;
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  const { data } = await apiClient.get<SessionDetail>(`/api/sessions/${sessionId}`);
  return data;
}

export async function submitQuery(sessionId: string, content: string): Promise<{ run_id: string }> {
  const { data } = await apiClient.post<{ run_id: string }>(`/api/sessions/${sessionId}/query`, { content });
  return data;
}

export function runEventsUrl(runId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  return `${base}/api/sessions/runs/${runId}/events`;
}
