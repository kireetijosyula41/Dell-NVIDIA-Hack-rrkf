import type { Scenario } from "@/lib/scenarios";
import { PanelTitle } from "./AgentOffice";

export function DecisionCard({
  scenario,
  approved,
  onApprove,
  onShowGraph,
  graphDisabled = false,
  compact = false,
}: {
  scenario: Scenario | null;
  approved: boolean;
  onApprove: () => void;
  onShowGraph?: () => void;
  graphDisabled?: boolean;
  compact?: boolean;
}) {
  if (!scenario) {
    return (
      <section className="glass flex min-h-[220px] flex-col p-4">
        <PanelTitle>CTO Decision & Ironic Report</PanelTitle>
        <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed p-6 text-center">
          <p className="mono text-xs tracking-widest text-muted-foreground">
            NO PENDING DECISIONS — TRIGGER A SCENARIO
          </p>
        </div>
      </section>
    );
  }

  const r = scenario.report;
  const glow = r.tone === "danger" ? "var(--neon-red)" : "var(--neon-emerald)";

  return (
    <section
      className={compact ? "" : "glass p-4"}
      style={{ "--glow": glow } as React.CSSProperties}
    >
      {!compact && <PanelTitle>CTO Decision & Ironic Report</PanelTitle>}
      <div className="glow-border animate-pop rounded-xl border bg-surface-2 p-0.5">
        <div
          className="mono rounded-t-[10px] px-4 py-3 text-sm font-bold tracking-[0.18em] text-background"
          style={{ background: glow }}
        >
          {r.banner}
        </div>
        <div className="space-y-3 p-4">
          {r.rows.map((row, i) => (
            <div
              key={row.label}
              className="rounded-lg border p-3"
              style={{
                borderColor:
                  i === 0
                    ? "color-mix(in oklab, var(--neon-red) 55%, transparent)"
                    : "color-mix(in oklab, var(--neon-amber) 55%, transparent)",
              }}
            >
              <p className="mono text-[10px] tracking-[0.2em] text-muted-foreground uppercase">
                {row.label}
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground/90">{row.value}</p>
            </div>
          ))}

          <div
            className="glow-border rounded-lg border bg-card p-4"
            style={{ "--glow": "var(--neon-blue)" } as React.CSSProperties}
          >
            <p className="mono text-[10px] tracking-[0.2em] text-muted-foreground uppercase">
              Agent Verdict // Chief of Staff
            </p>
            <p className="text-glow mt-2 text-base leading-relaxed font-semibold">{r.verdict}</p>
          </div>

          <button
            type="button"
            disabled={approved}
            onClick={onApprove}
            style={{ "--glow": glow } as React.CSSProperties}
            className="mono glow-border w-full rounded-xl border px-4 py-4 text-sm font-bold tracking-[0.12em] transition-all duration-200 hover:scale-[1.015] disabled:cursor-not-allowed disabled:opacity-60 sm:text-base"
          >
            <span className="text-glow">{approved ? "✅ EXECUTED & LOGGED TO memory.md" : r.action}</span>
          </button>
          {onShowGraph && (
            <button
              type="button"
              disabled={graphDisabled}
              onClick={onShowGraph}
              style={{ "--glow": "var(--neon-blue)" } as React.CSSProperties}
              className="mono glow-border w-full rounded-xl border px-4 py-3 text-xs font-bold tracking-[0.12em] transition-all hover:scale-[1.015] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="text-glow">VISUALIZE MONGODB EVIDENCE GRAPH</span>
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
