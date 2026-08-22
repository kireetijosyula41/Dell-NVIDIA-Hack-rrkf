# CEO Brain Evidence API

The API is the only data interface an agent needs. It exposes project search,
email search, graph neighborhoods, GitHub source metadata, audit creation, and
human decisions. It never imports `ground_truth.json`.

## Local development

Install dependencies in a virtual environment, then run:

```sh
uvicorn app.main:app --app-dir ceo-brain-api --reload --port 8080
```

Without MongoDB, the API reads generated JSON from `ceo-brain-project-graph/data`.
With MongoDB, set `MONGODB_URI` and it uses the database collections instead.

The API permits browser requests from local Vite development servers. Set
`CORS_ALLOW_ORIGINS=https://<truth-engine-host>` for a deployed UI origin. The
browser connects to this API only, never to MongoDB or the model server.

## GB10 deployment

From `ceo-brain-project-graph` after generating graph data and importing it:

```sh
NEMOCLAW_MODEL_ID=<operator-confirmed-model-id> docker compose up -d api
```

The model endpoint remains NemoClaw/OpenShell-managed. `NEMOCLAW_MODEL_ID` is
metadata displayed by the health endpoint and is not a hardcoded model choice.

## Test

```sh
PYTHONPATH=ceo-brain-api python -m unittest ceo-brain-api/tests/test_api.py
```
