import { Empty, Spin } from "antd";
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { colorForType } from "./colors";
import { useSubgraph } from "./useSubgraph";
import "./GraphPanel.css";

const ForceGraph2D = lazy(() => import("react-force-graph-2d"));

interface GraphPanelProps {
  sessionId: string;
  isActive: boolean;
}

export function GraphPanel({ sessionId, isActive }: GraphPanelProps) {
  const { data, isLoading } = useSubgraph(sessionId, isActive);
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => {
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const graphData = useMemo(
    () => ({
      nodes: data?.nodes.map((node) => ({ ...node })) ?? [],
      links:
        data?.edges.map((edge) => ({
          source: edge.source_id,
          target: edge.target_id,
          label: edge.type,
        })) ?? [],
    }),
    [data],
  );

  const types = useMemo(() => [...new Set((data?.nodes ?? []).map((node) => node.type))], [data]);

  return (
    <div className="graph-panel" ref={containerRef}>
      {isLoading && !data ? (
        <div className="graph-panel--centered">
          <Spin />
        </div>
      ) : graphData.nodes.length === 0 ? (
        <div className="graph-panel--centered">
          <Empty description="The graph fills in as the agent researches" />
        </div>
      ) : (
        <Suspense fallback={<div className="graph-panel--centered"><Spin /></div>}>
          <ForceGraph2D
            graphData={graphData}
            width={size.width || undefined}
            height={size.height || undefined}
            nodeId="id"
            nodeLabel="name"
            nodeColor={(node) => colorForType((node as { type: string }).type)}
            nodeRelSize={4}
            linkLabel="label"
            linkColor={() => "rgba(148, 163, 184, 0.35)"}
            linkDirectionalArrowLength={3}
            backgroundColor="transparent"
            cooldownTicks={80}
          />
        </Suspense>
      )}
      {types.length > 0 && (
        <div className="graph-legend">
          {types.map((type) => (
            <div key={type} className="graph-legend__item">
              <span className="graph-legend__swatch" style={{ background: colorForType(type) }} />
              {type}
            </div>
          ))}
        </div>
      )}
      {data && (
        <div className="graph-stats">
          {data.nodes.length} nodes · {data.edges.length} edges
        </div>
      )}
    </div>
  );
}
