import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Cpu, RotateCcw, ShieldCheck, Radio } from "lucide-react";

import { AgentOffice } from "@/components/mission/AgentOffice";
import { TerminalStream, type LogLine } from "@/components/mission/TerminalStream";
import { KanbanBoard, type Task } from "@/components/mission/KanbanBoard";
import { DecisionCard } from "@/components/mission/DecisionCard";
import { EvidenceGraph } from "@/components/mission/EvidenceGraph";
import { GitHubConnectionGate, PullRequestPreview } from "@/components/mission/DemoGitHubScreens";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { SCENARIOS, type AgentKey, type Scenario, playSuccessChime, stamp } from "@/lib/scenarios";
import { createAudit, getAudit, getEvidenceGraph, saveDecision, type Audit, type EvidenceGraph as EvidenceGraphData } from "@/lib/ceoBrainApi";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "OpenClaw Mission Control // OrgBrain" },
      {
        name: "description",
        content:
          "Air-gapped multi-agent mission control that audits meeting claims against ground truth and ships the patch.",
      },
      { property: "og:title", content: "OpenClaw Mission Control // OrgBrain" },
      {
        property: "og:description",
        content:
          "Live dashboard for the Meeting Room OrgBrain: agent office, OpenShell log stream, task board and CTO decision reports.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: MissionControl,
});

const STEP_MS = 1400;

function MissionControl() {
  const [lines, setLines] = useState<LogLine[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeAgent, setActiveAgent] = useState<AgentKey | null>(null);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [claim, setClaim] = useState<string | null>(null);
  const [review, setReview] = useState<Scenario | null>(null);
  const [approved, setApproved] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [running, setRunning] = useState(false);
  const [saved, setSaved] = useState(0);
  const [graph, setGraph] = useState<EvidenceGraphData | null>(null);
  const [graphOpen, setGraphOpen] = useState(false);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);
  const [selectedGraphNode, setSelectedGraphNode] = useState<string | null>(null);
  const [githubConnected, setGithubConnected] = useState(false);
  const [pullRequestOpen, setPullRequestOpen] = useState(false);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const videoRef = useRef<HTMLVideoElement>(null);
  const lineId = useRef(0);
  const auditIds = useRef<Record<string, string>>({});
  const auditStates = useRef<Record<string, Audit>>({});

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }, []);

  useEffect(() => clearTimers, [clearTimers]);

  const pushLine = (agent: AgentKey, tag: string, text: string) =>
    setLines((prev) => [...prev, { id: ++lineId.current, time: stamp(), tag, text, agent }]);

  const bootLines = (): LogLine[] => [
    { id: ++lineId.current, time: stamp(), tag: "System", text: "OpenClaw Gateway Connected on port 18789", agent: "chief" },
    { id: ++lineId.current, time: stamp(), tag: "System", text: "OpenShell sandbox ready · agents on standby", agent: "chief" },
  ];

  useEffect(() => {
    setLines(bootLines());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const reset = () => {
    clearTimers();
    toast.dismiss();
    setLines(bootLines());
    setTasks([]);
    setActiveAgent(null);
    setScenario(null);
    setClaim(null);
    setReview(null);
    setApproved(false);
    setModalOpen(false);
    setRunning(false);
    setGraph(null);
    setGraphOpen(false);
    setGraphLoading(false);
    setGraphError(null);
    setSelectedGraphNode(null);
    auditIds.current = {};
    auditStates.current = {};
    videoRef.current?.pause();
    if (videoRef.current) videoRef.current.currentTime = 0;
  };

  const applyAudit = (s: Scenario, audit: Audit) => {
    auditIds.current[s.id] = audit.auditId;
    auditStates.current[s.id] = audit;
    setReview((current) => current?.id === s.id ? {
      ...current,
      auditId: audit.auditId,
      auditStatus: audit.status,
      report: {
        ...current.report,
        verdict: audit.warning,
        rows: [
          ...current.report.rows.filter((row) => row.label !== "Evidence Status"),
          { label: "Evidence Status", value: `${audit.confidence.toUpperCase()} confidence | ${audit.projectIds.length} matching projects | ${audit.status}` },
        ],
      },
    } : current);
  };

  const pollAudit = (s: Scenario, auditId: string, attempts = 0) => {
    if (attempts >= 60) return;
    window.setTimeout(() => {
      void getAudit(auditId).then((audit) => {
        applyAudit(s, audit);
        if (audit.status === "warning_ready") {
          pushLine("audit", "NemoClaw", `Cited warning ready: ${audit.projectIds.length} evidence-linked projects.`);
        } else if (audit.status === "failed") {
          toast.error("NemoClaw audit failed", { description: audit.warning });
        } else {
          pollAudit(s, auditId, attempts + 1);
        }
      }).catch(() => pollAudit(s, auditId, attempts + 1));
    }, 1000);
  };

  const attachAudit = async (s: Scenario) => {
    try {
      const audit = await createAudit(s.audioClaim);
      applyAudit(s, audit);
      pushLine("audit", "MongoDB", `Evidence audit ${audit.status}: ${audit.projectIds.length} matching projects, ${audit.confidence} confidence.`);
      if (audit.status !== "warning_ready") pollAudit(s, audit.auditId);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "API unavailable";
      pushLine("chief", "System", `OrgBrain API unavailable: ${detail}`);
      toast.error("Evidence graph unavailable", { description: "Check the GB10 API URL and retry the scenario." });
    }
  };

  const runScenario = (s: Scenario) => {
    if (running || scenario) return;
    clearTimers();
    toast.dismiss();
    setLines(bootLines());
    setActiveAgent("vigil");
    setScenario(s);
    setClaim(s.audioClaim);
    setReview(null);
    setApproved(false);
    setModalOpen(false);
    setRunning(true);
    void attachAudit(s);
    setTasks((prev) => [
      ...prev.filter((t) => t.id !== s.id),
      { id: s.id, title: s.taskTitle, column: "inbox", scenario: s.button.toUpperCase() },
    ]);

    const move = (column: Task["column"]) =>
      setTasks((prev) => prev.map((t) => (t.id === s.id ? { ...t, column } : t)));

    s.logs.forEach((step, i) => {
      timers.current.push(
        setTimeout(
          () => {
            setActiveAgent(step.agent);
            pushLine(step.agent, step.tag, step.text);
            if (i === 1) move("auditing");
          },
          STEP_MS * (i + 1),
        ),
      );
    });

    timers.current.push(
      setTimeout(() => {
        setActiveAgent(null);
        setRunning(false);
        pushLine("chief", "System", "Meeting evidence collected. Awaiting meeting end before showing the audit report.");
      }, STEP_MS * (s.logs.length + 1)),
    );
  };

  const startMeetingAudit = () => runScenario(SCENARIOS[0]!);

  const finishMeetingAudit = () => {
    const s = scenario;
    if (!s || review) return;
    const move = (column: Task["column"]) =>
      setTasks((prev) => prev.map((task) => (task.id === s.id ? { ...task, column } : task)));
    move("review");
    setActiveAgent("chief");
    pushLine("chief", "Chief", "Meeting ended. Ground truth reconciled -> ESCALATING TO CTO FOR APPROVAL");
    const audit = auditStates.current[s.id];
    setReview({ ...s, ...(audit ? { auditId: audit.auditId, auditStatus: audit.status } : {}) });
    setModalOpen(true);
  };

  const approve = () => {
    if (!review || approved) return;
    setApproved(true);
    setTasks((prev) => prev.map((t) => (t.id === review.id ? { ...t, column: "done" } : t)));
    setActiveAgent(null);
    pushLine("forge", "Forge", `Executed: ${review.report.action.replace(/[[\]🟢🔴 ]+/g, " ").trim()}`);
    pushLine("chief", "System", `memory.md updated -> saved ${review.report.savings}`);
    setSaved((n) => n + 1);
    window.open("https://github.com/mithxr/google-research-mithxr", "_blank", "noopener,noreferrer");
    setPullRequestOpen(true);
    playSuccessChime();
    if (review.auditId) void saveDecision(review.auditId, "approved").catch(() => toast.error("Decision was not persisted to the GB10 API."));
    toast.success("PR Executed & Local Memory Updated!", {
      description: `$ Saved Recorded in memory.md — ${review.report.savings}`,
    });
    setModalOpen(false);
  };

  const showGraph = async () => {
    if (!review) return;
    setModalOpen(false);
    setGraphOpen(true);
    setGraphError(null);
    setGraph(null);
    setGraphLoading(true);
    try {
      const audit = review.auditId ? await getAudit(review.auditId) : await createAudit(review.audioClaim);
      applyAudit(review, audit);
      if (audit.status !== "warning_ready") {
        throw new Error("Evidence is still being collected. Keep the graph panel open and retry in a moment.");
      }
      const auditId = audit.auditId;
      const result = await getEvidenceGraph(auditId);
      setGraph(result);
      setSelectedGraphNode(result.highlightedNodeIds[0] ?? result.nodes[0]?.projectId ?? null);
    } catch (error) {
      setGraphError(error instanceof Error ? error.message : "The GB10 evidence API could not be reached.");
    } finally {
      setGraphLoading(false);
    }
  };

  if (!githubConnected) return <GitHubConnectionGate onConnect={() => setGithubConnected(true)} />;

  return (
    <main className="mx-auto flex min-h-screen max-w-[1600px] flex-col gap-4 p-4 lg:p-6">
      <header className="glass flex flex-wrap items-center justify-between gap-4 px-4 py-3">
        <div className="flex items-center gap-3">
          <span
            className="glow-border grid size-10 place-items-center rounded-lg border"
            style={{ "--glow": "var(--neon-blue)" } as React.CSSProperties}
          >
            <Radio className="size-5 text-primary" />
          </span>
          <div>
            <h1 className="mono text-sm font-bold tracking-[0.16em] sm:text-base">
              OPENCLAW MISSION CONTROL <span className="text-muted-foreground">//</span>{" "}
              <span className="text-glow" style={{ "--glow": "var(--neon-blue)" } as React.CSSProperties}>
                ORGBRAIN
              </span>
            </h1>
            <p className="mono text-[10px] tracking-[0.2em] text-muted-foreground uppercase">
              Multi-agent meeting room auditor · {saved} decisions executed
            </p>
          </div>
        </div>
        <div className="mono flex flex-wrap items-center gap-2 text-[10px] font-bold tracking-[0.14em]">
          <span
            className="glow-border flex items-center gap-2 rounded-full border px-3 py-1.5"
            style={{ "--glow": "var(--neon-emerald)" } as React.CSSProperties}
          >
            <ShieldCheck className="size-3.5 text-glow" />
            <span className="text-glow">OPENSHELL: ZERO-EGRESS AIR-GAPPED</span>
          </span>
          <span
            className="glow-border flex items-center gap-2 rounded-full border px-3 py-1.5"
            style={{ "--glow": "var(--neon-amber)" } as React.CSSProperties}
          >
            <Cpu className="size-3.5 text-glow" />
            <span className="text-glow">NVIDIA DGX SPARK (GB10)</span>
          </span>
        </div>
      </header>

      <section className="glass flex items-center justify-between gap-3 p-3">
        <p className="mono text-[10px] font-bold tracking-[0.18em] text-muted-foreground">MEETING INPUT // VIDEO-TRIGGERED AUDIT</p>
        <button
          type="button"
          onClick={reset}
          style={{ "--glow": "var(--neon-emerald)" } as React.CSSProperties}
          className="mono glow-border flex items-center gap-2 rounded-xl border bg-surface-2 px-4 py-3 text-[11px] font-bold tracking-[0.1em] transition-all duration-200 hover:scale-[1.02] sm:text-xs"
        >
          <RotateCcw className="text-glow size-3.5" />
          <span className="text-glow">🔄 RESET DEMO STATE</span>
        </button>
      </section>

      <section className="glass overflow-hidden p-3">
        <div className="mb-2 flex items-center justify-between"><p className="mono text-[10px] font-bold tracking-[0.18em] text-muted-foreground">LIVE MEETING FEED // PROJECT TITAN</p><span className="mono text-[9px] tracking-widest text-emerald-300">REPORT RELEASES WHEN MEETING ENDS</span></div>
        <video ref={videoRef} controls preload="metadata" onPlay={startMeetingAudit} onEnded={finishMeetingAudit} className="max-h-[420px] w-full rounded-lg border bg-black" src="/hackathona.mp4"><track kind="captions" /></video>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <AgentOffice activeAgent={activeAgent} />
        <TerminalStream lines={lines} claim={claim} />
        <KanbanBoard tasks={tasks} />
        <DecisionCard scenario={review} approved={approved} onApprove={approve} onShowGraph={showGraph} graphDisabled={graphLoading} />
      </div>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto border-none bg-transparent p-0 shadow-none">
          <DecisionCard scenario={review} approved={approved} onApprove={approve} onShowGraph={showGraph} graphDisabled={graphLoading} compact />
        </DialogContent>
      </Dialog>

      <Dialog open={graphOpen} onOpenChange={setGraphOpen}>
        <DialogContent className="max-h-[94vh] max-w-6xl overflow-y-auto border-none bg-transparent p-0 shadow-none">
          {graphLoading && <section className="glass p-10 text-center mono text-xs tracking-widest text-muted-foreground">QUERYING GB10 MONGODB EVIDENCE GRAPH...</section>}
          {graphError && <section className="glass p-8 text-center"><p className="mono text-xs tracking-widest text-destructive">EVIDENCE GRAPH UNAVAILABLE</p><p className="mt-2 text-sm text-muted-foreground">{graphError}</p><button type="button" onClick={showGraph} className="mono mt-4 rounded-lg border px-4 py-2 text-xs tracking-wider">RETRY GRAPH REQUEST</button></section>}
          {graph && <EvidenceGraph graph={graph} selectedId={selectedGraphNode} onSelect={setSelectedGraphNode} onClose={() => setGraphOpen(false)} />}
        </DialogContent>
      </Dialog>

      <Dialog open={pullRequestOpen} onOpenChange={setPullRequestOpen}>
        <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto border-none bg-transparent p-0 shadow-none">
          <PullRequestPreview onClose={() => setPullRequestOpen(false)} />
        </DialogContent>
      </Dialog>
    </main>
  );
}
