import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { getEvalRun, listEvalRuns, runEvaluation } from "../../api/eval";

export function useEval(sessionId: string) {
  const queryClient = useQueryClient();
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const runsQuery = useQuery({
    queryKey: ["eval-runs", sessionId],
    queryFn: () => listEvalRuns(sessionId),
  });

  const detailQuery = useQuery({
    queryKey: ["eval-run", sessionId, selectedRunId],
    queryFn: () => getEvalRun(sessionId, selectedRunId as string),
    enabled: selectedRunId !== null,
  });

  const triggerMutation = useMutation({
    mutationFn: (numQuestions: number) => runEvaluation(sessionId, numQuestions),
    onSuccess: (run) => {
      setSelectedRunId(run.run_id);
      queryClient.invalidateQueries({ queryKey: ["eval-runs", sessionId] });
    },
  });

  return {
    runs: runsQuery.data ?? [],
    isLoadingRuns: runsQuery.isLoading,
    selectedRunId,
    selectRun: setSelectedRunId,
    detail: detailQuery.data,
    isLoadingDetail: detailQuery.isFetching,
    triggerEval: triggerMutation.mutate,
    isTriggering: triggerMutation.isPending,
  };
}
