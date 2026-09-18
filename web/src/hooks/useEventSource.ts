import { useEffect } from "react";

type EventHandlers = Record<string, (data: unknown) => void>;

/**
 * Opens a native EventSource against `url` and wires named SSE events to `handlers`.
 * Reconnects whenever `url` changes; tears down on unmount or when `url` becomes null.
 */
export function useEventSource(url: string | null, handlers: EventHandlers): void {
  useEffect(() => {
    if (!url) return;

    const source = new EventSource(url);
    const entries = Object.entries(handlers);

    for (const [eventName, handler] of entries) {
      source.addEventListener(eventName, (event) => {
        const message = event as MessageEvent<string>;
        handler(message.data ? JSON.parse(message.data) : null);
      });
    }

    return () => source.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);
}
