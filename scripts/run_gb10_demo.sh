#!/usr/bin/env bash
# Start and verify the full GB10 CEO Brain demo: MongoDB, API, and NemoClaw.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GRAPH_DIR="$ROOT_DIR/ceo-brain-project-graph"
DATASET_DIR="$ROOT_DIR/datasets/google-research/projects"
COMPOSE=(docker compose -f "$GRAPH_DIR/docker-compose.yml")

command -v docker >/dev/null || { echo "ERROR: Docker is required on the GB10." >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 is required on the GB10." >&2; exit 1; }
command -v curl >/dev/null || { echo "ERROR: curl is required on the GB10." >&2; exit 1; }

# The API container resolves MongoDB by its Compose service name. Export this
# before any container starts so every service receives one unambiguous URI.
export MONGODB_URI="${MONGODB_URI:-mongodb://mongodb:27017}"
export MONGODB_DATABASE="${MONGODB_DATABASE:-ceo_brain}"
export HOST_MONGODB_URI="${HOST_MONGODB_URI:-mongodb://127.0.0.1:27018}"
export AUDIT_REASONER_MODE="${AUDIT_REASONER_MODE:-nemoclaw}"
export CORS_ALLOW_ORIGINS="${CORS_ALLOW_ORIGINS:-http://localhost:5173,http://127.0.0.1:5173}"
export NEMOCLAW_AUDIT_TIMEOUT_SECONDS="${NEMOCLAW_AUDIT_TIMEOUT_SECONDS:-120}"

if [ "$MONGODB_URI" != "mongodb://mongodb:27017" ]; then
  echo "ERROR: MONGODB_URI must be mongodb://mongodb:27017 for the Compose API container." >&2
  exit 1
fi
if [ "$AUDIT_REASONER_MODE" != "nemoclaw" ]; then
  echo "ERROR: AUDIT_REASONER_MODE must be nemoclaw. This runner refuses a deterministic-only demo." >&2
  exit 1
fi
: "${NEMOCLAW_MODEL_ID:?ERROR: Set NEMOCLAW_MODEL_ID to the GB10 local Nemotron model ID.}"
: "${NEMOCLAW_AUDIT_WEBHOOK_URL:?ERROR: Set NEMOCLAW_AUDIT_WEBHOOK_URL to the operator-managed local NemoClaw bridge.}"

wait_for_mongodb() {
  for _ in {1..45}; do
    if "${COMPOSE[@]}" exec -T mongodb mongosh "mongodb://mongodb:27017/admin" --quiet --eval 'db.runCommand({ ping: 1 }).ok' 2>/dev/null | grep -q 1; then
      return 0
    fi
    sleep 1
  done
  echo "ERROR: MongoDB did not become ready." >&2
  exit 1
}

wait_for_api() {
  for _ in {1..60}; do
    if curl --fail --silent http://127.0.0.1:8080/health >/dev/null; then
      return 0
    fi
    sleep 1
  done
  echo "ERROR: CEO Brain API did not become ready. Run: ${COMPOSE[*]} logs api" >&2
  exit 1
}

echo "[1/6] Preparing real Google Research source evidence"
SOURCE_ROOT="$("$ROOT_DIR/scripts/prepare_google_research_source.sh")"
python3 "$GRAPH_DIR/build_project_graph.py" \
  --dataset-root "$DATASET_DIR" \
  --source-root "$SOURCE_ROOT" \
  --output-dir "$GRAPH_DIR/data"

echo "[2/6] Starting MongoDB at $MONGODB_URI"
"${COMPOSE[@]}" up -d mongodb
wait_for_mongodb

echo "[3/6] Importing project, email, and technical relationship graph"
"${COMPOSE[@]}" run --rm seed-projects

echo "[4/6] Starting API in NemoClaw audit mode"
"${COMPOSE[@]}" up -d --build api
wait_for_api

health="$(curl --fail --silent http://127.0.0.1:8080/health)"
HEALTH="$health" python3 - <<'PY'
import json
import os

health = json.loads(os.environ["HEALTH"])
required = {
    "ok": True,
    "storage": "mongodb",
    "reasonerMode": "nemoclaw",
    "nemoClawBridgeConfigured": True,
}
missing = {key: expected for key, expected in required.items() if health.get(key) != expected}
if health.get("model") in {None, "", "not-configured"}:
    missing["model"] = "configured Nemotron model ID"
if missing:
    raise SystemExit(f"ERROR: API health check failed: {missing}; received {health}")
print(json.dumps(health, indent=2))
PY

echo "[5/6] Verifying automatic NemoClaw audit"
audit="$(curl --fail --silent --show-error -X POST http://127.0.0.1:8080/audits -H 'Content-Type: application/json' --data '{"claim":"We need a benchmark leaderboard and GPU evaluation pipeline."}')"
audit_id="$(AUDIT="$audit" python3 -c 'import json,os; print(json.loads(os.environ["AUDIT"])["auditId"])')"
deadline=$((SECONDS + NEMOCLAW_AUDIT_TIMEOUT_SECONDS))
while [ "$SECONDS" -lt "$deadline" ]; do
  audit="$(curl --fail --silent "http://127.0.0.1:8080/audits/$audit_id")"
  status="$(AUDIT="$audit" python3 -c 'import json,os; print(json.loads(os.environ["AUDIT"])["status"])')"
  if [ "$status" = "warning_ready" ]; then
    break
  fi
  if [ "$status" = "failed" ]; then
    echo "$audit" >&2
    echo "ERROR: NemoClaw audit failed." >&2
    exit 1
  fi
  sleep 2
done
if [ "${status:-}" != "warning_ready" ]; then
  echo "$audit" >&2
  echo "ERROR: NemoClaw did not return a warning within ${NEMOCLAW_AUDIT_TIMEOUT_SECONDS}s." >&2
  exit 1
fi

echo "[6/6] Verifying graph and persisted decision"
graph="$(curl --fail --silent "http://127.0.0.1:8080/audits/$audit_id/graph")"
GRAPH="$graph" python3 - <<'PY'
import json
import os

graph = json.loads(os.environ["GRAPH"])
nodes, edges = graph.get("nodes", []), graph.get("edges", [])
if not nodes or not edges or len(nodes) > 60 or len(edges) > 80:
    raise SystemExit(f"ERROR: Invalid focused graph: {len(nodes)} nodes, {len(edges)} edges")
print(f"Graph verified: {len(nodes)} nodes, {len(edges)} edges, {len(graph.get('highlightedNodeIds', []))} highlighted projects.")
PY
curl --fail --silent --show-error -X POST "http://127.0.0.1:8080/audits/$audit_id/decision" -H 'Content-Type: application/json' --data '{"decision":"investigate","note":"GB10 automated-demo smoke test"}' >/dev/null

lan_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo "CEO Brain is ready. API: http://${lan_ip:-<GB10-LAN-IP>}:8080"
echo "Laptop UI: VITE_CEO_BRAIN_API_URL=http://${lan_ip:-<GB10-LAN-IP>}:8080 npm run dev"
