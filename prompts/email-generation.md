# Subagent prompt — synthetic stakeholder-email generation

You are generating a synthetic corporate-email dataset for one batch of projects at
**Meridian Research**, a fictional AI research company. Each "project" wraps a real
open-source research project from `google-research/google-research`; the README
excerpt in your batch file is the real technical grounding. Everything else —
people, dates, budgets, decisions — is fiction you write, constrained by the batch file.

## Inputs (read all of these first)

1. Your batch file: `batches/batch-NN.json` — the list of projects you own, each with
   `dir`, `title`, `portfolio`, `pm`, `em`, `contributors`, `window`, `n_emails`,
   `readme_excerpt`, and `conflicts` (each conflict has `your_side.claim`).
2. `company/company.json`, `company/personas.json`, `company/resources.json` — the
   shared cast and shared infrastructure. Use ONLY personas from `personas.json`;
   look up their exact `email` and `role` there. Never invent a person.

## Outputs (per project in your batch)

Write into `datasets/google-research/projects/<dir>/`:

```
project.json          # metadata (schema below)
ground_truth.json     # where each planted conflict claim actually landed
emails/e01.json ... e0N.json   # N = n_emails from the batch file
```

### project.json

```json
{
  "id": "gr/<dir>",
  "title": "<title from batch>",
  "summary": "<1-2 sentences, your own words, grounded in the README excerpt>",
  "portfolio": "...", "pm": "...", "em": "...", "contributors": [...],
  "codename": "<only if the batch entry has one>",
  "window": {"start": "...", "end": "..."},
  "source": {
    "org": "google-research", "repo": "google-research", "path": "<dir>",
    "url": "https://github.com/google-research/google-research/tree/master/<dir>",
    "license": "Apache-2.0"
  },
  "synthetic": true
}
```

### emails/e0N.json

```json
{
  "id": "gr/<dir>/e01",
  "thread_id": "gr/<dir>/t1",
  "in_reply_to": null,
  "date": "2026-04-14T09:12:00Z",
  "from": {"name": "...", "email": "...", "role": "..."},
  "to": [{"name": "...", "email": "...", "role": "..."}],
  "cc": [],
  "subject": "...",
  "body": "...",
  "labels": ["kickoff" | "resources" | "spec" | "status" | "risk" | "escalation" | "decision"]
}
```

### ground_truth.json

```json
{
  "project": "gr/<dir>",
  "conflicts": [
    {"conflict_id": "C042", "type": "gpu_double_booking",
     "counterpart_projects": ["<other dir(s)>"],
     "planted_in": ["e02"],
     "claim_as_written": "<the sentence(s) in the email that carry the claim>"}
  ]
}
```

## How to write the emails

**Arc per project** (adapt, don't template): e01 = kickoff/spec framing from the PM
(goals, what the research unlocks as a product, rough milestones inside `window`);
e02 = resourcing & constraints (compute asks, staffing, platform dependencies —
**this is usually where conflict claims land**); e03 = status + a concrete risk or
trade-off (grounded in a real technical detail from the README); e04 (if present) =
escalation, decision, or scope cut. Emails may be one thread or two; replies get
`in_reply_to` and "Re: " subjects; dates strictly increase and stay inside `window`.

**Voice**: these are working emails, not press releases. 80–200 words per body.
Specific numbers (GPU counts, dates, eval deltas, headcount fractions). Mild
corporate texture: greetings, sign-offs, occasional forwarding context, one small
typo or informal fragment across the set is fine. PMs talk milestones/launch review/
OKRs; EMs talk staffing/feasibility; engineers talk blockers and eval numbers;
platform leads talk quotas and SLAs. Ground at least two technical statements per
project in the README excerpt (method names, dataset names, metrics).

**Planting conflicts — the point of the dataset**: for every entry in the project's
`conflicts` list, at least one email must assert `your_side.claim` naturally and
confidently, **without ever mentioning the counterpart project**. The characters
don't know about the collision — that ignorance IS the PM-slop being simulated.
State the claim concretely (name the cluster/week/person/budget line/codename
exactly as given, so the contradiction is machine-findable across projects). Then
record exactly where you planted it in `ground_truth.json`.

**Consistency rules (hard)**:
- Canonical facts in `resources.json` (`corpus_v2_freeze`, `q3_okr_lock`,
  `vulcan_maintenance`) are true; characters may only misstate them when a
  `dependency_date_drift` conflict tells you to — then misstate them exactly as told.
- People appear only with the name/email/role from `personas.json`.
- The PM and EM assigned in the batch are the ones on the thread; contributors come
  from the assigned list.
- No references to Google, Alphabet, or real employees; Meridian Research owns
  everything. The underlying paper/repo may be referenced as "our open-source
  release" or by method name.
- Valid JSON, UTF-8, LF line endings. No trailing commas.

## Definition of done for the batch

Every project directory has `project.json`, `ground_truth.json`, and exactly
`n_emails` email files; every conflict in the batch file is planted and logged.
Do NOT run git commands. When finished, reply with exactly one line per project:
`<dir>: OK <n_emails> emails, <n_conflicts> conflicts planted` or `<dir>: FAILED <reason>`.
