# CEO Brain: GB10 Run Instructions

## What This Starts

The GB10 runs MongoDB, the CEO Brain API, the real Google Research technical
graph builder, and the NemoClaw/OpenShell agent path. The laptop runs only the
Truth Engine UI.

`scripts/run_gb10_demo.sh` attempts NemoClaw first. If the bridge is missing,
the agent fails, or it times out, the script automatically restarts the API in
deterministic mode and still verifies the MongoDB graph and decision flow. Its
final output states exactly which mode powered the demo.

## Before Running

1. Clone or transfer this repository to the GB10.
2. Confirm Docker, Docker Compose, Git, Python 3, and Curl are installed.
3. Confirm Docker can pull `python:3.12-slim` and `mongo:8.0.29-noble`.
4. Configure NemoClaw/OpenShell with the intended local Nemotron model through
   `inference.local`.
5. Copy only `ceo-brain-nemoclaw` into the NemoClaw sandbox. Do not copy
   MongoDB credentials, GitHub write credentials, or `ground_truth.json`.
6. Start the operator-managed local NemoClaw bridge. It must accept the payload
   described in `ceo-brain-nemoclaw/BRIDGE_CONTRACT.md` and let the sandbox post
   the final warning to the CEO Brain API.

## Start The GB10 Stack

From the repository root, set the real model and bridge values, then run:

```sh
export NEMOCLAW_MODEL_ID=<GB10-local-Nemotron-model-ID>
export NEMOCLAW_AUDIT_WEBHOOK_URL=http://<GB10-local-NemoClaw-bridge>/audits
export AUDIT_REASONER_MODE=nemoclaw
export MONGODB_URI=mongodb://mongodb:27017
./scripts/run_gb10_demo.sh
```

The script performs six checks:

1. Sparse-checks out the 320 Google Research source paths and rebuilds the
   graph with real dependency/import/reference evidence.
2. Starts MongoDB with `MONGODB_URI=mongodb://mongodb:27017` inside Compose.
3. Imports projects, emails, and relationships into `ceo_brain`.
4. Attempts API health in NemoClaw mode when model and bridge values are set.
5. Sends a transcript claim and waits for NemoClaw to return `warning_ready`;
   on any failure it automatically restarts in deterministic fallback mode.
6. Verifies the focused graph and persists an investigation decision.

The script exits nonzero for a failed prerequisite, MongoDB/API failure, or
invalid graph. Missing or failed NemoClaw configuration activates the fallback.

## Start The Laptop UI

On the laptop, use the LAN IP printed by the GB10 script:

```sh
cd truth-engine-command
cp .env.example .env.local
# Set VITE_CEO_BRAIN_API_URL=http://<GB10-LAN-IP>:8080 in .env.local
npm run dev
```

Open the local Vite URL, run Scenario 1, then select
`VISUALIZE MONGODB EVIDENCE GRAPH`. The graph must open as a nodes-and-edges
overlay, not a text-only evidence status row.

## Troubleshooting

- `storage: json-fallback`: the API cannot reach Compose MongoDB; check
  `MONGODB_URI` is exactly `mongodb://mongodb:27017` for the API container.
- `nemoClawBridgeConfigured: false`: the runner will use deterministic fallback;
  export the bridge URL and rerun when you want the live agent path.
- Agent timeout: inspect the local bridge and NemoClaw sandbox logs. The graph
  demo remains available through the automatic deterministic fallback.
- Browser cannot load graph: confirm the laptop's `.env.local` uses the GB10
  LAN IP and set `CORS_ALLOW_ORIGINS=http://<laptop-host>:5173` before rerunning
  the GB10 script if the UI is not served as `localhost`.
