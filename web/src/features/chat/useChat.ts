import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { getSession, runEventsUrl, submitQuery } from "../../api/sessions";
import type { Message } from "../../api/types";
import { useEventSource } from "../../hooks/useEventSource";

export function useChat(sessionId: string) {
  const queryClient = useQueryClient();
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState("");

  const sessionQuery = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => getSession(sessionId),
  });

  const sendMutation = useMutation({
    mutationFn: (content: string) => submitQuery(sessionId, content),
    onSuccess: ({ run_id }) => {
      setStreamingText("");
      setActiveRunId(run_id);
      queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
    },
  });

  useEventSource(activeRunId ? runEventsUrl(activeRunId) : null, {
    "message-delta": (data) => {
      const { content } = data as { content: string };
      setStreamingText((prev) => prev + content);
    },
    "run-finished": () => {
      setActiveRunId(null);
      setStreamingText("");
      queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
    },
  });

  const messages: Message[] = sessionQuery.data?.messages ?? [];
  const isStreaming = activeRunId !== null;

  return {
    messages,
    isLoading: sessionQuery.isLoading,
    sendQuery: sendMutation.mutate,
    isSending: sendMutation.isPending,
    isStreaming,
    streamingText,
  };
}
