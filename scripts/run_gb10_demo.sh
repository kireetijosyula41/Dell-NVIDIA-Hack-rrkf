#!/usr/bin/env bash
# Prepare the MongoDB-backed CEO Brain demo on a GB10.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GRAPH_DIR="$ROOT_DIR/ceo-brain-project-graph"
DATASET_DIR="$ROOT_DIR/datasets/google-research/projects"

command -v docker >/dev/null || { echo "Docker is required on the GB10." >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required on the GB10." >&2; exit 1; }
command -v curl >/dev/null || { echo "curl is required on the GB10." >&2; exit 1; }

# These are deployment metadata and browser policy only. NemoClaw keeps model
# inference behind OpenShell's managed inference.local route.
export NEMOCLAW_MODEL_ID="${NEMOCLAW_MODEL_ID:-not-configured}"
export CORS_ALLOW_ORIGINS="${CORS_ALLOW_ORIGINS:-}"

echo "[1/4] Building runtime project graph data"
python3 "$GRAPH_DIR/build_project_graph.py" \
  --dataset-root "$DATASET_DIR" \
  --output-dir "$GRAPH_DIR/data"

echo "[2/4] Starting MongoDB and importing graph data"
docker compose -f "$GRAPH_DIR/docker-compose.yml" up -d mongodb
docker compose -f "$GRAPH_DIR/docker-compose.yml" run --rm seed-projects

echo "[3/4] Starting CEO Brain API"
docker compose -f "$GRAPH_DIR/docker-compose.yml" up -d --build api

echo "[4/4] Verifying API and MongoDB-backed audit flow"
for _ in {1..30}; do
  if curl --fail --silent http://127.0.0.1:8080/health >/dev/null; then
    break
  fi
  sleep 1
done

curl --fail --silent http://127.0.0.1:8080/health
echo
curl --fail --silent --show-error \
  -X POST http://127.0.0.1:8080/audits \
  -H 'Content-Type: application/json' \
  --data '{"claim":"We need a benchmark leaderboard and GPU evaluation pipeline."}'
echo

echo "CEO Brain is ready at http://<GB10-LAN-IP>:8080"
echo "Laptop UI: VITE_CEO_BRAIN_API_URL=http://<GB10-LAN-IP>:8080 npm run dev"
