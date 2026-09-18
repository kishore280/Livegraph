import { Empty, Spin } from "antd";
import type { Message } from "../../api/types";
import { Composer } from "./Composer";
import { MessageList } from "./MessageList";
import "./ChatPanel.css";

interface ChatPanelProps {
  messages: Message[];
  isLoading: boolean;
  sendQuery: (content: string) => void;
  isSending: boolean;
  isStreaming: boolean;
  streamingText: string;
}

export function ChatPanel({ messages, isLoading, sendQuery, isSending, isStreaming, streamingText }: ChatPanelProps) {
  if (isLoading) {
    return (
      <div className="chat-panel chat-panel--centered">
        <Spin />
      </div>
    );
  }

  return (
    <div className="chat-panel">
      {messages.length === 0 && !isStreaming ? (
        <div className="chat-panel--centered">
          <Empty description="Ask a question to start researching" />
        </div>
      ) : (
        <MessageList messages={messages} streamingText={streamingText} isStreaming={isStreaming} />
      )}
      <Composer onSend={sendQuery} disabled={isSending || isStreaming} />
    </div>
  );
}
