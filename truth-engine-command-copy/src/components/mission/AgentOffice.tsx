import { AGENTS, type AgentKey } from "@/lib/scenarios";

export function AgentOffice({ activeAgent }: { activeAgent: AgentKey | null }) {
  return (
    <section className="glass p-4">
      <PanelTitle>Agent Office</PanelTitle>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {AGENTS.map((a) => {
          const active = activeAgent === a.key;
          return (
            <article
              key={a.key}
              style={{ "--glow": a.glow } as React.CSSProperties}
              className={`relative overflow-hidden rounded-xl border bg-surface-2 p-4 transition-all duration-300 ${
                active ? "glow-border scale-[1.02]" : "border-border opacity-80"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="mono text-glow text-lg font-bold tracking-widest">{a.name}</h3>
                  <p className="text-xs font-medium text-foreground/80">{a.codename}</p>
                </div>
                <span
                  className={`mt-1 size-3 shrink-0 rounded-full ${active ? "animate-pulse-ring" : ""}`}
                  style={{ background: a.glow }}
                />
              </div>
              <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{a.role}</p>
              <div className="mono mt-3 flex items-center gap-2 text-[11px] tracking-widest">
                <span className={active ? "text-glow" : "text-muted-foreground"}>
                  {active ? a.active : a.idle}
                </span>
              </div>
              {active && (
                <div
                  className="pointer-events-none absolute inset-x-0 top-0 h-8 animate-scan opacity-40"
                  style={{
                    background: `linear-gradient(to bottom, transparent, color-mix(in oklab, ${a.glow} 40%, transparent), transparent)`,
                  }}
                />
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}

export function PanelTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mono mb-3 flex items-center gap-2 text-[11px] font-bold tracking-[0.25em] text-muted-foreground uppercase">
      <span className="inline-block h-3 w-1 rounded-full bg-primary" />
      {children}
    </h2>
  );
}
