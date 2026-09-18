import { Button, Collapse, Empty, Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEval } from "./useEval";
import type { EvalRunSummary } from "../../api/types";
import "./EvalPanel.css";

interface EvalPanelProps {
  sessionId: string;
}

const columns: ColumnsType<EvalRunSummary> = [
  { title: "Started", dataIndex: "started_at", render: (v: string) => new Date(v).toLocaleString() },
  { title: "Status", dataIndex: "status", render: (status: string) => <Tag>{status}</Tag> },
  { title: "Items", dataIndex: "completed_items", render: (_, row) => `${row.completed_items}/${row.total_items}` },
  {
    title: "Score",
    dataIndex: "overall_score",
    render: (score: number | null) => (score === null ? "—" : score.toFixed(2)),
  },
];

export function EvalPanel({ sessionId }: EvalPanelProps) {
  const { runs, isLoadingRuns, selectedRunId, selectRun, detail, isLoadingDetail, triggerEval, isTriggering } =
    useEval(sessionId);

  return (
    <div className="eval-panel">
      <div className="eval-panel__header">
        <span className="eval-panel__title">Evaluation runs</span>
        <Button type="primary" loading={isTriggering} onClick={() => triggerEval(5)}>
          Run evaluation
        </Button>
      </div>

      <Table<EvalRunSummary>
        size="small"
        rowKey="run_id"
        loading={isLoadingRuns}
        columns={columns}
        dataSource={runs}
        pagination={false}
        onRow={(row) => ({ onClick: () => selectRun(row.run_id) })}
        rowClassName={(row) => (row.run_id === selectedRunId ? "eval-panel__row--selected" : "")}
        locale={{ emptyText: <Empty description="No evaluation runs yet" /> }}
      />

      {selectedRunId && (
        <div className="eval-panel__detail">
          {isLoadingDetail && !detail ? (
            "Loading…"
          ) : detail ? (
            <Collapse
              items={detail.items.map((item) => ({
                key: item.item_index,
                label: item.query_text,
                children: (
                  <div className="eval-panel__item">
                    <p>
                      <strong>Gold:</strong> {item.gold_answer}
                    </p>
                    <p>
                      <strong>Generated:</strong> {item.generated_answer}
                    </p>
                    <div className="eval-panel__metrics">
                      {Object.entries(item.metrics).map(([key, value]) => (
                        <Tag key={key}>
                          {key}: {typeof value === "number" ? value.toFixed(2) : value}
                        </Tag>
                      ))}
                    </div>
                  </div>
                ),
              }))}
            />
          ) : null}
        </div>
      )}
    </div>
  );
}
