import { SendOutlined } from "@ant-design/icons";
import { Button, Input } from "antd";
import { useState } from "react";
import "./Composer.css";

interface ComposerProps {
  onSend: (content: string) => void;
  disabled: boolean;
}

export function Composer({ onSend, disabled }: ComposerProps) {
  const [draft, setDraft] = useState("");

  function handleSubmit() {
    const content = draft.trim();
    if (!content || disabled) return;
    onSend(content);
    setDraft("");
  }

  return (
    <div className="composer">
      <Input.TextArea
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onPressEnter={(event) => {
          if (event.shiftKey) return;
          event.preventDefault();
          handleSubmit();
        }}
        placeholder="Ask the agent to research something…"
        autoSize={{ minRows: 1, maxRows: 6 }}
        disabled={disabled}
      />
      <Button
        type="primary"
        icon={<SendOutlined />}
        onClick={handleSubmit}
        disabled={disabled || !draft.trim()}
      />
    </div>
  );
}
