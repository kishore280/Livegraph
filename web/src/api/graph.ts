import { apiClient } from "./client";
import type { Subgraph } from "./types";

export async function getSubgraph(sessionId: string, maxNodes = 200): Promise<Subgraph> {
  const { data } = await apiClient.get<Subgraph>(`/api/graph/${sessionId}/subgraph`, {
    params: { max_nodes: maxNodes },
  });
  return data;
}
