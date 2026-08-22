#!/usr/bin/env bash
# Start and verify CEO Brain on a GB10, preferring NemoClaw with a demo fallback.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GRAPH_DIR="$ROOT_DIR/ceo-brain-project-graph"
DATASET_DIR="$ROOT_DIR/datasets/google-research/projects"
COMPOSE=(docker compose -f "$GRAPH_DIR/docker-compose.yml")

command -v docker >/dev/null || { echo "ERROR: Docker is required on the GB10." >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 is required on the GB10." >&2; exit 1; }
command -v curl >/dev/null || { echo "ERROR: curl is required on the GB10." >&2; exit 1; }

# The Compose API resolves MongoDB by its service name, before any service starts.
export MONGODB_URI="${MONGODB_URI:-mongodb://mongodb:27017}"
export MONGODB_DATABASE="${MONGODB_DATABASE:-ceo_brain}"
export HOST_MONGODB_URI="${HOST_MONGODB_URI:-mongodb://127.0.0.1:27018}"
export CORS_ALLOW_ORIGINS="${CORS_ALLOW_ORIGINS:-http://localhost:5173,http://127.0.0.1:5173}"
export NEMOCLAW_AUDIT_TIMEOUT_SECONDS="${NEMOCLAW_AUDIT_TIMEOUT_SECONDS:-120}"

if [ "$MONGODB_URI" != "mongodb://mongodb:27017" ]; then
  echo "ERROR: MONGODB_URI must be mongodb://mongodb:27017 for the Compose API container." >&2
  exit 1
fi

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

start_api() {
  "${COMPOSE[@]}" up -d --build --force-recreate api
  wait_for_api
}

create_audit() {
  curl --fail --silent --show-error -X POST http://127.0.0.1:8080/audits \
    -H 'Content-Type: application/json' \
    --data '{"claim":"We need a benchmark leaderboard and GPU evaluation pipeline."}'
}

audit_id_from() {
  AUDIT="$1" python3 -c 'import json,os; print(json.loads(os.environ["AUDIT"])["auditId"])'
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

demo_reasoner="deterministic"
audit=""
audit_id=""

if [ -n "${NEMOCLAW_MODEL_ID:-}" ] && [ -n "${NEMOCLAW_AUDIT_WEBHOOK_URL:-}" ]; then
  echo "[4/6] Attempting NemoClaw audit mode"
  export AUDIT_REASONER_MODE="nemoclaw"
  start_api
  health="$(curl --fail --silent http://127.0.0.1:8080/health)"
  if HEALTH="$health" python3 - <<'PY'
import json
import os
health = json.loads(os.environ["HEALTH"])
assert health.get("storage") == "mongodb"
assert health.get("reasonerMode") == "nemoclaw"
assert health.get("nemoClawBridgeConfigured") is True
assert health.get("model") not in {None, "", "not-configured"}
PY
  then
    if audit="$(create_audit)"; then
      audit_id="$(audit_id_from "$audit")"
      deadline=$((SECONDS + NEMOCLAW_AUDIT_TIMEOUT_SECONDS))
      status="pending_agent_review"
      while [ "$SECONDS" -lt "$deadline" ]; do
        if ! audit="$(curl --fail --silent "http://127.0.0.1:8080/audits/$audit_id")"; then
          break
        fi
        status="$(AUDIT="$audit" python3 -c 'import json,os; print(json.loads(os.environ["AUDIT"])["status"])')"
        [ "$status" = "warning_ready" ] && break
        [ "$status" = "failed" ] && break
        sleep 2
      done
      if [ "${status:-}" = "warning_ready" ]; then
        demo_reasoner="nemoclaw"
        echo "NemoClaw audit verified."
      else
        echo "WARNING: NemoClaw did not reach warning_ready; switching to deterministic fallback." >&2
      fi
    else
      echo "WARNING: NemoClaw audit could not be created; switching to deterministic fallback." >&2
    fi
  else
    echo "WARNING: NemoClaw health configuration is incomplete; switching to deterministic fallback." >&2
  fi
else
  echo "WARNING: NEMOCLAW_MODEL_ID or NEMOCLAW_AUDIT_WEBHOOK_URL is missing; using deterministic fallback." >&2
fi

if [ "$demo_reasoner" != "nemoclaw" ]; then
  echo "[4/6] Starting deterministic fallback mode"
  export AUDIT_REASONER_MODE="deterministic"
  export NEMOCLAW_AUDIT_WEBHOOK_URL=""
  start_api
  health="$(curl --fail --silent http://127.0.0.1:8080/health)"
  HEALTH="$health" python3 - <<'PY'
import json
import os
health = json.loads(os.environ["HEALTH"])
if health.get("storage") != "mongodb" or health.get("reasonerMode") != "deterministic":
    raise SystemExit(f"ERROR: deterministic fallback API health failed: {health}")
PY
  audit="$(create_audit)"
  audit_id="$(audit_id_from "$audit")"
  status="$(AUDIT="$audit" python3 -c 'import json,os; print(json.loads(os.environ["AUDIT"])["status"])')"
  [ "$status" = "warning_ready" ] || { echo "ERROR: deterministic audit did not become ready." >&2; exit 1; }
fi

echo "[5/6] Verifying graph from $demo_reasoner audit"
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

echo "[6/6] Verifying persisted human decision"
curl --fail --silent --show-error -X POST "http://127.0.0.1:8080/audits/$audit_id/decision" \
  -H 'Content-Type: application/json' \
  --data "{\"decision\":\"investigate\",\"note\":\"GB10 $demo_reasoner demo smoke test\"}" >/dev/null

lan_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo "CEO Brain is ready using: $demo_reasoner"
echo "API: http://${lan_ip:-<GB10-LAN-IP>}:8080"
echo "Laptop UI: VITE_CEO_BRAIN_API_URL=http://${lan_ip:-<GB10-LAN-IP>}:8080 npm run dev"
