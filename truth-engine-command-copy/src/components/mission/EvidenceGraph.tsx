import { ExternalLink, Network, X } from "lucide-react";

import type { EvidenceGraph as EvidenceGraphData, GraphNode } from "@/lib/ceoBrainApi";
import { PanelTitle } from "./AgentOffice";

const DOMAIN_COLORS: Record<string, string> = {
  agent_orchestration: "var(--neon-purple)",
  evaluation: "var(--neon-amber)",
  foundation_models: "var(--neon-blue)",
  generative_media: "var(--neon-red)",
  multimodal: "var(--neon-blue)",
  search_retrieval: "var(--neon-emerald)",
  vision: "var(--neon-amber)",
};

function nodeColor(node: GraphNode) {
  return DOMAIN_COLORS[node.domains[0] ?? ""] ?? "var(--neon-emerald)";
}

function positions(nodes: GraphNode[], highlighted: Set<string>) {
  const center = { x: 450, y: 260 };
  const focus = nodes.filter((node) => highlighted.has(node.projectId));
  const others = nodes.filter((node) => !highlighted.has(node.projectId));
  const result = new Map<string, { x: number; y: number }>();
  const place = (items: GraphNode[], radius: number, offset = 0) => {
    items.forEach((node, index) => {
      const angle = offset + (Math.PI * 2 * index) / Math.max(items.length, 1);
      result.set(node.projectId, { x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius * 0.68 });
    });
  };
  if (focus.length === 1) result.set(focus[0]!.projectId, center);
  else place(focus, 112, -Math.PI / 2);
  place(others, 220, -Math.PI / 2 + 0.22);
  return result;
}

function nodeLabel(node: GraphNode) {
  return node.title.length > 22 ? `${node.title.slice(0, 21)}...` : node.title;
}

export function EvidenceGraph({ graph, onClose, selectedId, onSelect }: {
  graph: EvidenceGraphData;
  onClose: () => void;
  selectedId: string | null;
  onSelect: (projectId: string) => void;
}) {
  const highlighted = new Set(graph.highlightedNodeIds);
  const nodeById = new Map(graph.nodes.map((node) => [node.projectId, node]));
  const layout = positions(graph.nodes, highlighted);
  const selected = nodeById.get(selectedId ?? "") ?? nodeById.get(graph.highlightedNodeIds[0] ?? "") ?? graph.nodes[0];

  return (
    <section className="glass animate-fade-up overflow-hidden p-4" style={{ "--glow": "var(--neon-blue)" } as React.CSSProperties}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <PanelTitle><Network className="size-3.5" />MongoDB Evidence Graph</PanelTitle>
          <p className="mono -mt-2 mb-3 text-[10px] tracking-[0.12em] text-muted-foreground">
            {graph.nodes.length} PROJECTS // {graph.edges.length} EVIDENCE-LINKED RELATIONSHIPS
          </p>
        </div>
        <button type="button" onClick={onClose} className="mono rounded-lg border px-3 py-2 text-[10px] tracking-widest hover:bg-surface-2">
          <X className="mr-1 inline size-3.5" /> CLOSE GRAPH
        </button>
      </div>
      {graph.nodes.length === 0 ? (
        <div className="rounded-xl border border-dashed p-10 text-center mono text-xs tracking-widest text-muted-foreground">NO EVIDENCE-LINKED PROJECTS FOUND</div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_300px]">
          <div className="min-h-[430px] overflow-hidden rounded-xl border bg-[radial-gradient(circle_at_50%_45%,oklch(0.29_0.07_252/.7),transparent_48%),oklch(0.15_0.025_265)]">
            <svg viewBox="0 0 900 520" className="h-full min-h-[430px] w-full" role="img" aria-label="MongoDB project evidence graph">
              <defs>
                <marker id="evidence-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--neon-blue)" /></marker>
              </defs>
              {graph.edges.map((edge) => {
                const from = layout.get(edge.fromProject);
                const to = layout.get(edge.toProject);
                if (!from || !to) return null;
                const emphasized = highlighted.has(edge.fromProject) || highlighted.has(edge.toProject);
                return <line key={`${edge.fromProject}-${edge.toProject}-${edge.relationType}`} x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={emphasized ? "var(--neon-blue)" : "oklch(0.6 0.05 245 / .45)"} strokeWidth={emphasized ? 2.4 : 1} strokeDasharray={edge.source === "inferred" ? "5 5" : undefined} markerEnd="url(#evidence-arrow)" />;
              })}
              {graph.nodes.map((node) => {
                const position = layout.get(node.projectId);
                if (!position) return null;
                const active = selected?.projectId === node.projectId;
                const focus = highlighted.has(node.projectId);
                return (
                  <g key={node.projectId} transform={`translate(${position.x} ${position.y})`} className="cursor-pointer" onClick={() => onSelect(node.projectId)}>
                    {focus && <circle r="31" fill={nodeColor(node)} opacity=".18" />}
                    <circle r={focus ? 20 : 14} fill="var(--surface-2)" stroke={nodeColor(node)} strokeWidth={active ? 4 : focus ? 3 : 1.5} />
                    <circle r="4" fill={nodeColor(node)} />
                    <text y={focus ? 38 : 29} textAnchor="middle" fill="currentColor" className="fill-foreground font-mono text-[10px]">{nodeLabel(node)}</text>
                  </g>
                );
              })}
            </svg>
          </div>
          {selected && <aside className="rounded-xl border bg-surface-2 p-4">
            <p className="mono text-[10px] tracking-[0.18em] text-muted-foreground">SELECTED PROJECT</p>
            <h3 className="mt-2 text-lg font-bold leading-tight">{selected.title}</h3>
            <p className="mt-3 text-sm leading-relaxed text-foreground/80">{selected.summary}</p>
            <div className="mt-4 flex flex-wrap gap-1.5">{selected.domains.map((domain) => <span key={domain} className="mono rounded border px-2 py-1 text-[9px] tracking-wider" style={{ borderColor: nodeColor(selected), color: nodeColor(selected) }}>{domain.replaceAll("_", " ")}</span>)}</div>
            {selected.source.url && <a className="mono mt-4 flex items-center gap-1 text-[10px] tracking-wider text-primary hover:underline" href={selected.source.url} target="_blank" rel="noreferrer"><ExternalLink className="size-3" /> GITHUB SOURCE</a>}
            <div className="mt-5 border-t pt-3"><p className="mono text-[10px] tracking-[0.18em] text-muted-foreground">LINKED EVIDENCE</p>{graph.evidence.filter((item) => item.projectId === selected.projectId).slice(0, 3).map((item, index) => <p key={`${item.emailId ?? item.url ?? index}`} className="mt-2 text-xs leading-relaxed text-foreground/80">{item.kind?.toUpperCase()}: {item.detail ?? item.emailId ?? "Source evidence"}</p>)}</div>
          </aside>}
        </div>
      )}
      <p className="mono mt-3 text-[9px] tracking-wider text-muted-foreground">SOLID = VERIFIED EVIDENCE // DASHED = INFERRED DOMAIN OVERLAP // HIGHLIGHTED = AUDIT MATCH</p>
    </section>
  );
}
