export type AgentKey = "vigil" | "audit" | "forge" | "chief";

export type AgentDef = {
  key: AgentKey;
  name: string;
  codename: string;
  role: string;
  glow: string;
  idle: string;
  active: string;
};

export const AGENTS: AgentDef[] = [
  {
    key: "vigil",
    name: "VIGIL",
    codename: "Signal Sentinel",
    role: "Audio Ingestion & Intent Router",
    glow: "var(--neon-blue)",
    idle: "STANDBY",
    active: "LISTENING",
  },
  {
    key: "audit",
    name: "AUDIT",
    codename: "Ground-Truth Auditor",
    role: "Git Repo & Log Scanner",
    glow: "var(--neon-amber)",
    idle: "IDLE",
    active: "AUDITING",
  },
  {
    key: "forge",
    name: "FORGE",
    codename: "Patch Builder",
    role: "Code Diff Generator",
    glow: "var(--neon-emerald)",
    idle: "IDLE",
    active: "PATCHING",
  },
  {
    key: "chief",
    name: "CHIEF",
    codename: "Chief of Staff",
    role: "Orchestrator & Approval Manager",
    glow: "var(--neon-purple)",
    idle: "MONITORING",
    active: "AWAITING APPROVAL",
  },
];

export type LogStep = { agent: AgentKey; tag: string; text: string };

export type ReportRow = { label: string; value: string };

export type Scenario = {
  id: string;
  auditId?: string;
  auditStatus?: string;
  button: string;
  taskTitle: string;
  audioClaim: string;
  logs: LogStep[];
  report: {
    title: string;
    banner: string;
    rows: ReportRow[];
    verdict: string;
    action: string;
    tone: "safe" | "danger";
    savings: string;
  };
};

export const SCENARIOS: Scenario[] = [
  {
    id: "s1",
    button: "Scenario 1: Re-Inventing Wheel",
    taskTitle: "Project Titan — New Queue Service",
    audioClaim:
      "Team, we're kicking off Project Titan! We need to build a brand-new internal notification and queue service from the ground up.",
    logs: [
      { agent: "vigil", tag: "Vigil", text: "Audio Ingested -> Event: NEW_PRODUCT_PROPOSAL" },
      { agent: "audit", tag: "OpenShell", text: "Sandboxed Audit: Scanning local git trees..." },
      { agent: "audit", tag: "Audit", text: "MATCH FOUND: /packages/core-pubsub (Shipped 8 months ago)" },
      {
        agent: "audit",
        tag: "Audit",
        text: "INBOX MATCH: 4 other teams requested access to core-pubsub last week.",
      },
      { agent: "forge", tag: "Forge", text: "Generated Pull Request: import @internal/core-pubsub" },
    ],
    report: {
      title: "PROJECT TITAN PROPOSAL REPORT",
      banner: "🚨 PROJECT TITAN PROPOSAL REPORT",
      rows: [
        { label: "PM Estimate", value: "4 Engineers | 160 Hours | $32,000 Budget | Delivery: Q4" },
        { label: "Required Accesses", value: "AWS SQS, GCP PubSub, PagerDuty Admin" },
      ],
      verdict:
        "Bro, you can literally npm install @internal/core-pubsub. It's been running in production for 240 days. I created a PR importing it into your repo. You're welcome.",
      action: "[ 🟢 APPROVE PR & SAVE $32,000 ]",
      tone: "safe",
      savings: "$32,000",
    },
  },
  {
    id: "s2",
    button: "Scenario 2: Prod Fire",
    taskTitle: "Product Phoenix — 'Zero Downtime' Claim",
    audioClaim:
      "Product Phoenix launched yesterday! It's running smooth as butter in production, zero downtime, time to celebrate!",
    logs: [
      { agent: "vigil", tag: "Vigil", text: "Audio Ingested -> Event: STATUS_CLAIM_STABLE" },
      {
        agent: "audit",
        tag: "Audit",
        text: "Querying BQL Logs... ALERT: 14,200 '500 Internal Server Errors'",
      },
      { agent: "audit", tag: "Audit", text: "Scanning Support Inbox... ALERT: 18 angry emails from VP of Sales" },
      {
        agent: "forge",
        tag: "Forge",
        text: "Fetching Local Runbooks... Drafting Git Revert Patch to Tag v1.4.2",
      },
    ],
    report: {
      title: "PRODUCTION REALITY CHECK",
      banner: "🚨 PRODUCTION REALITY CHECK",
      rows: [
        { label: "Dev Claim", value: "Smooth as butter, zero issues." },
        {
          label: "Ground Truth",
          value:
            "14,200 database deadlocks logged, 18 high-priority support tickets, CTO inbox is on fire.",
        },
      ],
      verdict:
        "Developer is delusional. Production is actively burning. I drafted an emergency Git Rollback to tag v1.4.2 and executed the emergency runbook.",
      action: "[ 🔴 APPROVE EMERGENCY ROLLBACK & REVERT ]",
      tone: "danger",
      savings: "1 production outage",
    },
  },
  {
    id: "s3",
    button: "Scenario 3: Cloud GPU Waste",
    taskTitle: "Sentiment Model — 8x H100 Request",
    audioClaim:
      "Our customer feedback sentiment model is getting slow. We need to provision 8x H100 GPU instances on AWS for $15,000/month to keep up.",
    logs: [
      { agent: "vigil", tag: "Vigil", text: "Audio Ingested -> Event: INFRASTRUCTURE_REQUEST" },
      { agent: "audit", tag: "Audit", text: "Analyzing code complexity: sentiment_classifier.py" },
      {
        agent: "audit",
        tag: "Audit",
        text: "AST Result: Sentiment script is running a 3,000-line IF-ELSE regex loop.",
      },
      { agent: "forge", tag: "Forge", text: "Refactoring regex to 3B local model on DGX Spark via Ollama." },
    ],
    report: {
      title: "INFRASTRUCTURE AUDIT REPORT",
      banner: "🚨 INFRASTRUCTURE AUDIT REPORT",
      rows: [
        { label: "PM Request", value: "$15,000/month AWS Cloud Provisioning ($180,000/year)" },
        {
          label: "Agent Discovery",
          value:
            "You are trying to rent an H100 GPU cluster to run a nested IF/ELSE statement written in 2021.",
        },
      ],
      verdict:
        "I refactored the regex into a 3B local model running on our DGX Spark inside OpenShell for $0.00. I auto-declined the AWS cloud request.",
      action: "[ 🟢 APPROVE LOCAL REFACTOR & CANCEL AWS ]",
      tone: "safe",
      savings: "$180,000/yr",
    },
  },
  {
    id: "s4",
    button: "Scenario 4: 6-Month Refactor",
    taskTitle: "Billing Service — Rust Rewrite Proposal",
    audioClaim:
      "Our billing service codebase is technical debt hell. We need a 6-month complete feature freeze to rewrite the entire system in Rust.",
    logs: [
      { agent: "vigil", tag: "Vigil", text: "Audio Ingested -> Event: CODEBASE_REWRITE_PROPOSAL" },
      { agent: "audit", tag: "Audit", text: "AST Analysis: 94% of bugs originate from ONE 600-line file." },
      { agent: "audit", tag: "Audit", text: "Git Blame: billing_parser.py written by Dave in 2023." },
      {
        agent: "forge",
        tag: "Forge",
        text: "Rewriting billing_parser.py into clean modular Python. Passing 48/48 unit tests.",
      },
    ],
    report: {
      title: "ENGINEERING REFACTOR REPORT",
      banner: "🚨 ENGINEERING REFACTOR REPORT",
      rows: [
        { label: "Dev Request", value: "6 Months Code Freeze | 1,000 Engineering Hours | $150,000 Lost Velocity" },
        {
          label: "Agent Discovery",
          value:
            "The entire codebase isn't broken. Just billing_parser.py written by Dave in 2023 while sleep-deprived.",
        },
      ],
      verdict:
        "I refactored Dave's file in 1.4 seconds. All unit tests passed. You can keep shipping features on Monday.",
      action: "[ 🟢 APPROVE REFACTOR & CANCEL CODE FREEZE ]",
      tone: "safe",
      savings: "$150,000",
    },
  },
];

export function stamp(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `[${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}]`;
}

export function playSuccessChime() {
  try {
    const Ctx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new Ctx();
    const now = ctx.currentTime;
    [660, 880, 1320].forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, now + i * 0.09);
      gain.gain.exponentialRampToValueAtTime(0.12, now + i * 0.09 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + i * 0.09 + 0.3);
      osc.connect(gain).connect(ctx.destination);
      osc.start(now + i * 0.09);
      osc.stop(now + i * 0.09 + 0.35);
    });
    setTimeout(() => void ctx.close(), 900);
  } catch {
    /* audio unavailable */
  }
}
