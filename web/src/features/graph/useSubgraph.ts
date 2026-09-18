import { useQuery } from "@tanstack/react-query";
import { getSubgraph } from "../../api/graph";

const POLL_INTERVAL_MS = 4000;

export function useSubgraph(sessionId: string, isActive: boolean) {
  return useQuery({
    queryKey: ["subgraph", sessionId],
    queryFn: () => getSubgraph(sessionId),
    refetchInterval: isActive ? POLL_INTERVAL_MS : false,
  });
}
