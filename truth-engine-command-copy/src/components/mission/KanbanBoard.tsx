import { Check } from "lucide-react";
import { PanelTitle } from "./AgentOffice";

export type Column = "inbox" | "auditing" | "review" | "done";

export type Task = { id: string; title: string; column: Column; scenario: string };

const COLUMNS: { key: Column; label: string; glow: string }[] = [
  { key: "inbox", label: "Inbox", glow: "var(--neon-blue)" },
  { key: "auditing", label: "Auditing", glow: "var(--neon-amber)" },
  { key: "review", label: "Review (Action Needed)", glow: "var(--neon-purple)" },
  { key: "done", label: "Done", glow: "var(--neon-emerald)" },
];

export function KanbanBoard({ tasks }: { tasks: Task[] }) {
  return (
    <section className="glass p-4">
      <PanelTitle>Interactive Task Board</PanelTitle>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {COLUMNS.map((col) => {
          const items = tasks.filter((t) => t.column === col.key);
          return (
            <div
              key={col.key}
              style={{ "--glow": col.glow } as React.CSSProperties}
              className="flex min-h-[150px] flex-col rounded-xl border bg-surface-2 p-2"
            >
              <p className="mono text-glow mb-2 text-[10px] font-bold tracking-widest uppercase">
                {col.label} · {items.length}
              </p>
              <div className="flex flex-col gap-2">
                {items.map((t) => (
                  <div
                    key={t.id}
                    className="glow-border animate-pop rounded-lg border bg-card p-2.5 text-xs font-medium"
                  >
                    <div className="flex items-start gap-2">
                      {col.key === "done" && (
                        <Check className="text-glow mt-0.5 size-4 shrink-0 animate-pop" strokeWidth={3} />
                      )}
                      <span className={col.key === "done" ? "text-foreground/70 line-through" : ""}>
                        {t.title}
                      </span>
                    </div>
                    <p className="mono mt-1.5 text-[10px] tracking-widest text-muted-foreground">
                      {t.scenario}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
