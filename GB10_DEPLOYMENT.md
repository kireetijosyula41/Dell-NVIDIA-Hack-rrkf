# CEO Brain GB10 Deployment

## 1. Transfer the project

Clone the repository on the GB10 or transfer it from the prepared external SSD.
Do not transfer local `node_modules`, Python virtual environments, Docker volumes,
or `ground_truth.json` into the NemoClaw workspace.

## 2. Build project graph data

```sh
cd ceo-brain-project-graph
python3 build_project_graph.py \
  --dataset-root ../datasets/google-research/projects \
  --output-dir data
```

## 3. Start MongoDB and API

```sh
export NEMOCLAW_MODEL_ID=<operator-confirmed-nemotron-model-id>
docker compose up -d mongodb
docker compose run --rm seed-projects
docker compose up -d --build api
curl http://127.0.0.1:8080/health
```

The API runs on port `8080`. Configure the laptop UI with
`VITE_CEO_BRAIN_API_URL=http://<GB10-IP>:8080`.

## 4. Configure NemoClaw

Onboard NemoClaw using the GB10 operator's local Nemotron endpoint and model ID.
OpenShell keeps the sandbox model route at `inference.local`. Copy the contents of
`ceo-brain-nemoclaw` into the sandbox workspace and allow-list only the CEO Brain
API route required by `CEO_BRAIN_API_URL`.

The sandbox must use the read-only tool client. It must not receive MongoDB
credentials, GitHub write credentials, or any `ground_truth.json` files.

## 5. Demo check

1. Open the Truth Engine UI on the laptop.
2. Enter a meeting claim in `RUN LIVE AUDIT`.
3. Confirm the warning card has project/email/GitHub evidence.
4. Select `SHOW EVIDENCE GRAPH`.
5. Confirm the graph contains at most 60 nodes and 80 edges.
6. Record an approval or investigation decision.
