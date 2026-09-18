import { Spin, Tabs } from "antd";
import { lazy, Suspense } from "react";
import { useParams } from "react-router-dom";
import { ChatPanel } from "../features/chat/ChatPanel";
import { useChat } from "../features/chat/useChat";
import { GraphPanel } from "../features/graph/GraphPanel";
import "./SessionPage.css";

const EvalPanel = lazy(() => import("../features/eval/EvalPanel").then((m) => ({ default: m.EvalPanel })));

export function SessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const chat = useChat(sessionId as string);

  return (
    <div className="session-page">
      <div className="session-page__chat">
        <ChatPanel {...chat} />
      </div>
      <div className="session-page__side">
        <Tabs
          className="session-page__tabs"
          items={[
            {
              key: "graph",
              label: "Knowledge graph",
              children: <GraphPanel sessionId={sessionId as string} isActive={chat.isStreaming} />,
            },
            {
              key: "eval",
              label: "Evaluation",
              children: (
                <Suspense fallback={<Spin />}>
                  <EvalPanel sessionId={sessionId as string} />
                </Suspense>
              ),
            },
          ]}
        />
      </div>
    </div>
  );
}
