export interface Message {
  role: "user" | "model";
  content: string;
  timestamp: Date;
  payload?: QueryResponsePayload;
}

export interface ReasoningStep {
  id: number;
  title: string;
  description: string;
  status: "pending" | "active" | "completed";
  code?: string;
}

export interface TraceEntry {
  ts?: string;
  node?: string;
  details?: Record<string, unknown>;
}

export interface QueryResponsePayload {
  session_id: string;
  answer: string;
  needs_clarification: boolean;
  clarification_question?: string | null;
  sql_query?: string | null;
  sql_validation_error?: string | null;
  result_records: Array<Record<string, unknown>>;
  chart_spec: Record<string, unknown>;
  quality_report: Record<string, unknown>;
  board_map: Record<string, unknown>;
  board_schemas: Array<Record<string, unknown>>;
  table_schemas: Record<string, Array<Record<string, unknown>>>;
  traces: TraceEntry[];
  conversation_history_length?: number;
  history_backend?: string;
}

interface QueryRequestPayload {
  question: string;
  conversation_history: Array<{ role: string; content: string }>;
  session_id?: string;
}

function apiBaseUrl() {
  const explicit = import.meta.env.VITE_BACKEND_URL as string | undefined;
  if (explicit && explicit.trim()) {
    return explicit.trim().replace(/\/+$/, "");
  }
  return "/api";
}

export async function queryFounderBI(
  question: string,
  conversationHistory: Array<{ role: string; content: string }>,
  sessionId: string
): Promise<QueryResponsePayload> {
  const payload: QueryRequestPayload = {
    question,
    conversation_history: conversationHistory,
    session_id: sessionId,
  };

  const response = await fetch(`${apiBaseUrl()}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Backend query failed (${response.status}): ${text}`);
  }

  return (await response.json()) as QueryResponsePayload;
}

const SESSION_KEY = "founder_bi_session_id";

export function getOrCreateSessionId() {
  const existing = window.localStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const generated = window.crypto.randomUUID();
  window.localStorage.setItem(SESSION_KEY, generated);
  return generated;
}

function titleFromNode(node: string) {
  return node
    .split("_")
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(" ");
}

export function tracesToReasoningSteps(traces: TraceEntry[]): ReasoningStep[] {
  if (!traces.length) return [];
  return traces.map((trace, idx) => {
    const node = trace.node || `step_${idx + 1}`;
    const details = trace.details || {};
    const keys = Object.keys(details).slice(0, 4);
    const description =
      keys.length > 0
        ? `Details: ${keys.join(", ")}`
        : "Trace captured from backend node execution.";

    return {
      id: idx + 1,
      title: titleFromNode(node),
      description,
      status: "completed",
      code: JSON.stringify(details, null, 2).slice(0, 900),
    };
  });
}

export function loadingReasoningSteps(): ReasoningStep[] {
  return [
    { id: 1, title: "Query Decomposition", description: "Analyzing user intent...", status: "active" },
    { id: 2, title: "Schema Discovery", description: "Resolving strict monday boards...", status: "pending" },
    { id: 3, title: "Live Data Fetch", description: "Running live monday API calls...", status: "pending" },
    { id: 4, title: "SQL Planning", description: "Generating or selecting safe SQL...", status: "pending" },
    { id: 5, title: "Insight Synthesis", description: "Preparing final answer and caveats...", status: "pending" },
  ];
}
