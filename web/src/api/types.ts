export interface Message {
  id: number;
  session_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  run_id: string | null;
}

export interface ResearchSession {
  id: number;
  session_id: string;
  created_at: string;
}

export interface SessionDetail extends ResearchSession {
  messages: Message[];
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
}

export interface GraphEdge {
  id: string;
  source_id: string;
  target_id: string;
  type: string;
}

export interface Subgraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface EvalRunSummary {
  run_id: string;
  session_id: string;
  status: string;
  overall_score: number | null;
  metrics: Record<string, number>;
  total_items: number;
  completed_items: number;
  started_at: string;
  completed_at: string | null;
}

export interface EvalRunItem {
  item_index: number;
  query_text: string;
  gold_answer: string;
  generated_answer: string;
  retrieved_chunk_ids: string[];
  gold_chunk_ids: string[];
  metrics: Record<string, number | string>;
}

export interface EvalRunDetail extends EvalRunSummary {
  items: EvalRunItem[];
}
