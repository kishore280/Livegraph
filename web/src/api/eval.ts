import { apiClient } from "./client";
import type { EvalRunDetail, EvalRunSummary } from "./types";

export async function runEvaluation(sessionId: string, numQuestions = 5): Promise<EvalRunDetail> {
  const { data } = await apiClient.post<EvalRunDetail>(`/api/sessions/${sessionId}/eval`, {
    num_questions: numQuestions,
  });
  return data;
}

export async function listEvalRuns(sessionId: string): Promise<EvalRunSummary[]> {
  const { data } = await apiClient.get<{ runs: EvalRunSummary[] }>(`/api/sessions/${sessionId}/eval`);
  return data.runs;
}

export async function getEvalRun(sessionId: string, runId: string): Promise<EvalRunDetail> {
  const { data } = await apiClient.get<EvalRunDetail>(`/api/sessions/${sessionId}/eval/${runId}`);
  return data;
}
