import { useEffect, useRef } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "../../api/types";
import "./MessageList.css";

interface MessageListProps {
  messages: Message[];
  streamingText: string;
  isStreaming: boolean;
}

export function MessageList({ messages, streamingText, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, streamingText]);

  return (
    <div className="message-list">
      {messages.map((message) => (
        <div key={message.id} className={`message-row message-row--${message.role}`}>
          <span className="message-role">{message.role === "user" ? "you" : "agent"}</span>
          <div className="message-content">
            <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
          </div>
        </div>
      ))}
      {isStreaming && (
        <div className="message-row message-row--assistant">
          <span className="message-role">agent</span>
          <div className="message-content">
            <Markdown remarkPlugins={[remarkGfm]}>{streamingText}</Markdown>
            <span className="message-cursor" />
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
