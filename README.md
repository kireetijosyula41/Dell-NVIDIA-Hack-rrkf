# OrgBrain

OrgBrain is a live meeting-room intelligence system that helps leaders detect duplicate work, hidden dependencies, and avoidable delivery cost before a new project is approved. It connects a meeting claim to evidence from Google Research source code, synthetic project emails, and a MongoDB relationship graph, then presents a focused, human-reviewable audit.

The demo runs the evidence and agent stack on an NVIDIA GB10. Truth Engine runs on a laptop as the presentation UI. A meeting video triggers an audit; when the meeting ends, OrgBrain presents a grounded Project Titan recommendation and lets the presenter open the evidence graph or approve a simulated pull request.

## What We Built

- **Live meeting flow:** `hackathona.mp4` is the Project Titan meeting input. Playback starts the audit; its report is released only after the meeting ends.
- **NemoClaw audit path:** a GB10-hosted NemoClaw agent uses a locally served Nemotron model through OpenShell's managed `inference.local` route. It can inspect only allow-listed evidence tools and returns a cited warning through a schema-validated callback.
- **MongoDB project-evidence graph:** 320 Google Research project nodes, 1,257 synthetic emails, and technical relationships built from real dependency manifests, source imports, GitHub references, functional domains, and shared resource claims.
- **Focused graph UI:** Truth Engine requests only the one-to-three-hop neighborhood associated with an audit. The SVG graph highlights relevant projects and exposes GitHub and email evidence when a node is selected.
- **Human-in-the-loop approval:** an approver records a decision in MongoDB and opens a clearly labeled simulated pull request. No automated GitHub writes occur.
- **Demo resilience:** if the NemoClaw bridge or local model route is not available, the GB10 runner switches to a deterministic, evidence-backed fallback that uses the same audit and graph API contract.

## Architecture

```text
Truth Engine UI (laptop)
  |  POST /audits, GET /audits/{id}/graph, POST /audits/{id}/decision
  v
OrgBrain API (GB10 :8080)
  |---------------------> MongoDB
  |                         projects, emails, relationships, audits, decisions
  |
  +--> NemoClaw audit bridge --> OpenShell sandbox --> local Nemotron model
         |                         |
         |                         +--> read-only OrgBrain evidence tools
         +--> POST /tools/create-audit-warning
```

The model never receives MongoDB credentials, GitHub write credentials, or `ground_truth.json`. It interacts with evidence through the API's restricted tool facade. The backend validates project IDs, citations, confidence, and the warning schema before an audit becomes ready for the UI.

## Audit Flow

1. The presenter starts the Project Titan meeting video in Truth Engine.
2. The UI sends the selected meeting claim to `POST /audits` on the GB10.
3. OrgBrain ranks relevant projects, collects matching emails, and retrieves a bounded relationship neighborhood from MongoDB.
4. NemoClaw/Nemotron reviews the read-only evidence tools and submits a cited warning with confidence, project IDs, and a recommended action.
5. When the meeting ends, Truth Engine displays the Project Titan audit report.
6. `VISUALIZE MONGODB EVIDENCE GRAPH` fetches and renders the focused evidence graph, including highlighted paths and node-level source/email evidence.
7. The presenter records a human decision and may open the simulated PR view.

## Evidence Graph

Each main graph node is a dataset project ID such as `gr/CoDi`, not merely a top-level GitHub repository. Every project stores its Google Research source path, README-derived summary, functional domains, resources, and linked email IDs.

Relationships include:

- declared package or framework dependencies
- parsed Python, JavaScript, and TypeScript imports
- local cross-project imports and Google Research source references
- shared datasets, models, frameworks, and resource claims
- functional-domain overlap, including queue, notification, tracking, search, agent, evaluation, ML platform, analytics, security, identity, workflow, observability, storage, data pipeline, and developer tooling domains

Every edge includes its relationship type, evidence, and whether it is verified or inferred. The audit graph is capped at 60 nodes and 80 edges to keep the decision view legible.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `truth-engine-command/` | Laptop presentation UI, meeting video flow, audit card, and evidence graph. |
| `ceo-brain-api/` | FastAPI service exposing audit, evidence-tool, graph, health, and decision endpoints. |
| `ceo-brain-project-graph/` | Graph builder, MongoDB Compose stack, import tooling, and generated graph data. |
| `ceo-brain-nemoclaw/` | NemoClaw agent instructions, read-only tool client, and bridge callback contract. |
| `openclaw-google-research-agent/` | OpenClaw research analyst workspace for source-backed Google Research discovery. |
| `datasets/google-research/projects/` | Curated project metadata and synthetic email dataset. |
| `scripts/run_gb10_demo.sh` | End-to-end GB10 graph build, MongoDB import, API startup, agent check, and fallback verification. |

The legacy directory names are retained for deployment compatibility; the product name displayed to users is **OrgBrain**.

## Run On The GB10

From the repository root, configure the GB10's local model and operator-managed NemoClaw bridge, then run the deployment script:

```bash
export NEMOCLAW_MODEL_ID="<GB10-local-Nemotron-model-id>"
export NEMOCLAW_AUDIT_WEBHOOK_URL="http://127.0.0.1:<bridge-port>/audits"
export AUDIT_REASONER_MODE=nemoclaw
export MONGODB_URI=mongodb://mongodb:27017

./scripts/run_gb10_demo.sh
```

The runner:

1. prepares Google Research source evidence and rebuilds the technical graph;
2. starts MongoDB and imports projects, emails, relationships, and indexes;
3. starts the API and checks `storage: mongodb`;
4. submits a representative meeting claim to the NemoClaw bridge;
5. waits for a schema-valid `warning_ready` audit;
6. verifies a bounded graph response and persists a sample decision.

If the bridge is unavailable or times out, the runner explicitly restarts in deterministic fallback mode and completes the same MongoDB-backed smoke test. It prints the API's GB10 LAN address when ready.

Full operator instructions are in [INSTRUCTIONS_FOR_GB10.md](INSTRUCTIONS_FOR_GB10.md) and [GB10_DEPLOYMENT.md](GB10_DEPLOYMENT.md).

## Run The UI On A Laptop

Use the GB10 LAN IP printed by the runner:

```bash
cd truth-engine-command
printf 'VITE_CEO_BRAIN_API_URL=http://<GB10-LAN-IP>:8080\n' > .env.local
npm install
npm run dev
```

Open the local Vite URL, enter the simulated GitHub Enterprise access screen, play the meeting video, wait for it to finish, and then open the Project Titan report. Select `VISUALIZE MONGODB EVIDENCE GRAPH` to inspect the evidence path. The approval action records a MongoDB decision, opens the simulated PR overlay, and links to <https://github.com/mithxr/google-research-mithxr>.

## Verification

The GB10 deployment is successful when:

- `GET /health` reports `storage: "mongodb"` and the active reasoner mode;
- MongoDB contains 320 projects, 1,257 emails, and technical relationship edges;
- `POST /audits` returns an audit with cited evidence and project IDs;
- `GET /audits/{auditId}/graph` returns a non-empty graph within the 60-node, 80-edge display limit;
- a human decision is persisted through `POST /audits/{auditId}/decision`;
- Truth Engine on the laptop can reach the GB10 API over the event LAN.

## Safety Model

OrgBrain is an evidence assistant, not an autonomous executor. It presents grounded findings for a human to evaluate. The NemoClaw sandbox is read-only: it can search project and email evidence, inspect a bounded graph, retrieve cached GitHub excerpts, and submit a structured warning. It cannot access database credentials, modify GitHub, send email, or access evaluation ground truth.
