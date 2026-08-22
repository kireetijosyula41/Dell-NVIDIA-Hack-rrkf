# CEO Brain Project-Evidence Graph

Build runtime graph data without exposing `ground_truth.json`:

```sh
python3 build_project_graph.py \
  --dataset-root ../datasets/google-research/projects \
  --output-dir data
```

Import the generated project, email, domain, and relationship documents:

```sh
docker compose up -d mongodb
docker compose run --rm seed-projects
```

The `ground_truth.json` files remain outside the output directory and are reserved for evaluation.
