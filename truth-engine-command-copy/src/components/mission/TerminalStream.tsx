import { useEffect, useRef } from "react";
import { PanelTitle } from "./AgentOffice";
import type { AgentKey } from "@/lib/scenarios";

export type LogLine = { id: number; time: string; tag: string; text: string; agent: AgentKey };

const TAG_GLOW: Record<string, string> = {
  Vigil: "var(--neon-blue)",
  Audit: "var(--neon-amber)",
  Forge: "var(--neon-emerald)",
  OpenShell: "var(--neon-purple)",
  Chief: "var(--neon-purple)",
  System: "var(--neon-emerald)",
};

export function TerminalStream({ lines, claim }: { lines: LogLine[]; claim: string | null }) {
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    boxRef.current?.scrollTo({ top: boxRef.current.scrollHeight, behavior: "smooth" });
  }, [lines.length]);

  return (
    <section className="glass flex min-h-0 flex-col p-4">
      <PanelTitle>Real-Time Event Feed // OpenShell Stream</PanelTitle>
      {claim && (
        <div
          className="mb-3 animate-fade-up rounded-lg border bg-surface-2 p-3"
          style={{ "--glow": "var(--neon-blue)" } as React.CSSProperties}
        >
          <p className="mono text-[10px] tracking-[0.2em] text-muted-foreground">AUDIO CLAIM CAPTURED</p>
          <p className="mt-1 text-sm text-foreground/90 italic">“{claim}”</p>
        </div>
      )}
      <div
        ref={boxRef}
        className="mono h-[280px] flex-1 overflow-y-auto rounded-lg border bg-[oklch(0.16_0.03_265)] p-3 text-[12.5px] leading-relaxed shadow-inner lg:h-auto"
      >
        {lines.length === 0 ? (
          <p className="text-muted-foreground">
            openshell@dgx-spark:~$ awaiting scenario trigger<span className="animate-pulse">▋</span>
          </p>
        ) : (
          lines.map((l) => (
            <p key={l.id} className="animate-fade-up break-words">
              <span className="text-muted-foreground">{l.time} </span>
              <span
                className="font-bold"
                style={{ "--glow": TAG_GLOW[l.tag] ?? "var(--neon-blue)" } as React.CSSProperties}
              >
                <span className="text-glow">[{l.tag}]</span>
              </span>{" "}
              <span className="text-foreground/85">{l.text}</span>
            </p>
          ))
        )}
      </div>
    </section>
  );
}
