import { CheckCircle2, Github, LockKeyhole, ShieldCheck } from "lucide-react";

export function GitHubConnectionGate({ onConnect }: { onConnect: () => void }) {
  return (
    <main className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_15%_10%,oklch(0.3_0.1_235/.3),transparent_30%),radial-gradient(circle_at_85%_90%,oklch(0.3_0.1_160/.2),transparent_30%),oklch(0.13_0.025_265)] p-5">
      <section className="w-full max-w-md overflow-hidden rounded-2xl border border-white/15 bg-[oklch(0.19_0.035_265/.96)] shadow-2xl">
        <div className="border-b border-white/10 bg-black/25 p-7 text-center">
          <div className="mx-auto grid size-14 place-items-center rounded-full bg-white text-black"><Github className="size-8" /></div>
          <p className="mono mt-5 text-[10px] tracking-[0.25em] text-muted-foreground">ORGBRAIN INTERNAL TOOL ACCESS</p>
          <h1 className="mt-2 text-2xl font-bold">Connect GitHub Enterprise</h1>
          <p className="mt-2 text-sm text-muted-foreground">Authorize read-only project evidence access for this demo.</p>
        </div>
        <div className="space-y-4 p-6">
          <label className="block"><span className="mono text-[10px] tracking-widest text-muted-foreground">USERNAME</span><input className="mt-1.5 w-full rounded-lg border bg-black/25 px-3 py-2.5 text-sm outline-none focus:border-primary" defaultValue="ceo@google-research.internal" readOnly /></label>
          <label className="block"><span className="mono text-[10px] tracking-widest text-muted-foreground">PASSWORD</span><input className="mt-1.5 w-full rounded-lg border bg-black/25 px-3 py-2.5 text-sm outline-none focus:border-primary" defaultValue="demo-only-token" type="password" readOnly /></label>
          <button type="button" onClick={onConnect} className="mono glow-border mt-2 w-full rounded-lg border px-4 py-3 text-xs font-bold tracking-[0.15em]" style={{ "--glow": "var(--neon-emerald)" } as React.CSSProperties}>
            <LockKeyhole className="mr-2 inline size-4" /> ENTER ORGBRAIN
          </button>
          <p className="flex items-center justify-center gap-1.5 text-center text-[11px] text-muted-foreground"><ShieldCheck className="size-3.5 text-emerald-400" /> Simulated demo login. No credentials are captured or sent.</p>
        </div>
      </section>
    </main>
  );
}

export function PullRequestPreview({ onClose }: { onClose: () => void }) {
  return (
    <section className="overflow-hidden rounded-xl border border-slate-700 bg-[#0d1117] text-slate-200 shadow-2xl">
      <header className="border-b border-slate-700 bg-[#161b22] px-6 py-5">
        <div className="flex items-center gap-2 text-sm"><Github className="size-5" /><span className="font-semibold">mithxr</span><span className="text-slate-500">/</span><span className="font-semibold">google-research-mithxr</span></div>
        <p className="mono mt-4 text-[10px] tracking-widest text-amber-300">SIMULATED DEMO PULL REQUEST - NO EXTERNAL WRITE</p>
        <h2 className="mt-2 text-xl font-semibold">Reuse existing evaluation infrastructure for Project Titan</h2>
        <p className="mt-2 text-sm text-slate-400">orgbrain/reuse-project-titan wants to merge 1 commit into master</p>
      </header>
      <div className="grid gap-4 p-6 md:grid-cols-[1fr_220px]">
        <div className="overflow-hidden rounded-lg border border-slate-700"><div className="border-b border-slate-700 bg-[#161b22] px-4 py-2 mono text-[11px]">project_titan/reuse_evaluation.py</div><pre className="overflow-x-auto p-4 text-xs leading-6"><code><span className="text-red-300">- build_leaderboard_from_scratch()</span>{"\n"}<span className="text-emerald-300">+ from shared_evaluation import benchmark_leaderboard</span>{"\n"}<span className="text-emerald-300">+ benchmark_leaderboard.reuse_for(&quot;project-titan&quot;)</span></code></pre></div>
        <aside className="rounded-lg border border-slate-700 bg-[#161b22] p-4"><p className="mono text-[10px] tracking-widest text-slate-400">ORGBRAIN VERDICT</p><p className="mt-3 text-sm leading-relaxed">Existing evidence graph identified reusable evaluation infrastructure and linked project/email evidence.</p><div className="mt-4 flex items-center gap-2 text-sm text-emerald-300"><CheckCircle2 className="size-4" /> $32,000 avoided</div></aside>
      </div>
      <footer className="flex justify-end border-t border-slate-700 p-4"><button type="button" onClick={onClose} className="rounded-lg bg-[#238636] px-4 py-2 text-sm font-semibold text-white">Close simulated PR</button></footer>
    </section>
  );
}
