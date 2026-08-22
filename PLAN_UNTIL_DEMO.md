# CEO Brain Plan Until Demo

## Goal

Demo a scripted meeting video in Truth Engine. A selected transcript claim goes
to the GB10, NemoClaw gathers read-only project/email/GitHub evidence, and the
UI displays a warning plus the focused MongoDB evidence graph.

## 1. Graph UI First

1. Copy `truth-engine-command/.env.example` to `.env.local`, set
   `VITE_CEO_BRAIN_API_URL=http://<GB10-IP>:8080`, then run `npm run dev`.
2. Put the demo video at `truth-engine-command/public/demo-meeting.mp4`.
3. Run Scenario 1. It creates an API audit from the scenario transcript.
4. Wait for `warning_ready`, then select `VISUALIZE MONGODB EVIDENCE GRAPH`.
5. Verify the graph loads from `GET /audits/{id}/graph`, highlights matched
   projects, and shows source/email evidence when a node is clicked.
6. Verify unavailable API and empty graph states show a retry message rather
   than fabricated data.

## 2. GB10 Readiness

1. Run `NEMOCLAW_MODEL_ID=<model-id> ./scripts/run_gb10_demo.sh` on the GB10.
2. Verify `/health` reports `storage: mongodb`.
3. Verify MongoDB contains 320 projects, 1,257 emails, and relationship edges.
4. Run the API test suite with `MONGODB_URI=mongodb://localhost:27018`.
5. Confirm the laptop can access the GB10 API over the event LAN and CORS
   preflight succeeds.

## 3. Automatic NemoClaw Audit

1. Configure the NemoClaw sandbox with the GB10 operator's model ID and
   OpenShell-managed `inference.local` route.
2. Copy `ceo-brain-nemoclaw` into the sandbox; do not copy `ground_truth.json`.
3. Configure `AUDIT_REASONER_MODE=nemoclaw` and the local
   `NEMOCLAW_AUDIT_WEBHOOK_URL`.
4. The API creates `pending_agent_review`, sends the audit ID and claim to the
   bridge, and streams status events.
5. The agent uses only read-only evidence tools and submits a cited warning for
   the original audit ID. `warning_ready` enables the graph in Truth Engine.
6. Keep `AUDIT_REASONER_MODE=deterministic` as the explicit emergency fallback.

## 4. Rehearsal

1. Rehearse Scenario 1 three times: video cue, transcript audit, warning,
   evidence graph, and human decision.
2. Rehearse an unrelated claim; it must return low confidence and `defer`.
3. Disable public GitHub/network and verify cached MongoDB evidence still works.
4. Confirm graphs are bounded to 60 nodes and 80 edges.
5. Record the GB10 LAN IP, model ID, health response, and known-good audit ID
   in presenter notes.

## Acceptance Checklist

- The laptop UI never connects directly to MongoDB or the model server.
- Graph nodes and edges are returned by the GB10 API, not UI mock data.
- Agent warnings contain citations and update the same audit ID.
- The sandbox has no MongoDB credentials, GitHub write access, or ground truth.
- A decision persists through `POST /audits/{id}/decision`.
