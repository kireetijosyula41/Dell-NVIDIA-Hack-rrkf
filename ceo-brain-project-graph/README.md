# CEO Brain Project-Evidence Graph

Build runtime graph data from a sparse Google Research source checkout without
exposing `ground_truth.json`:

```sh
../scripts/prepare_google_research_source.sh
python3 build_project_graph.py \
  --dataset-root ../datasets/google-research/projects \
  --source-root ../.cache/google-research-source \
  --output-dir data
```

The builder stores project manifests/imports and creates verified edges for
local project imports, GitHub source references, shared declared dependencies,
and shared source imports. It still records email/resource and functional-domain
relationships separately.

Import the generated project, email, domain, and relationship documents:

```sh
docker compose up -d mongodb
docker compose run --rm seed-projects
```

The `ground_truth.json` files remain outside the output directory and are reserved for evaluation.
