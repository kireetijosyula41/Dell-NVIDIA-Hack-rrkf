export type Evidence = {
  kind?: string;
  projectId?: string;
  emailId?: string;
  url?: string;
  detail?: string;
};

export type GraphNode = {
  projectId: string;
  title: string;
  summary: string;
  domains: string[];
  portfolio?: string;
  source: { url?: string; path?: string };
};

export type GraphEdge = {
  fromProject: string;
  toProject: string;
  relationType: string;
  confidence: number;
  source: "verified" | "inferred";
  evidence: Evidence[];
};

export type EvidenceGraph = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightedNodeIds: string[];
  evidence: Evidence[];
};

export type Audit = {
  auditId: string;
  status: string;
  warning: string;
  confidence: "low" | "medium" | "high";
  projectIds: string[];
  evidence: Evidence[];
  recommendedAction: "investigate" | "reuse" | "defer" | "approve";
};

const configuredBaseUrl = import.meta.env["VITE_CEO_BRAIN_API_URL"]?.trim();
const baseUrl = (configuredBaseUrl || "http://localhost:8080").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    const detail = body.startsWith("<!DOCTYPE html") ? "endpoint not found; check VITE_CEO_BRAIN_API_URL" : body.slice(0, 240) || "request failed";
    throw new Error(`OrgBrain API ${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export function createAudit(claim: string): Promise<Audit> {
  return request<Audit>("/audits", {
    method: "POST",
    body: JSON.stringify({ claim }),
  });
}

export function getEvidenceGraph(auditId: string): Promise<EvidenceGraph> {
  return request<EvidenceGraph>(`/audits/${encodeURIComponent(auditId)}/graph`);
}

export function getAudit(auditId: string): Promise<Audit> {
  return request<Audit>(`/audits/${encodeURIComponent(auditId)}`);
}

export function saveDecision(auditId: string, decision: "approved" | "deferred" | "investigate"): Promise<unknown> {
  return request(`/audits/${encodeURIComponent(auditId)}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision }),
  });
}
