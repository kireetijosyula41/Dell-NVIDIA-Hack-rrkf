# CEO Brain Repository Graph

This directory builds the MongoDB-ready repository knowledge graph used by CEO Brain.

## Create the graph data

```sh
python3 build_repository_graph.py --limit 50 --output-dir data
```

Set `GITHUB_TOKEN` before running to raise GitHub API limits. The collector uses the
organization repository listing plus public raw files, so it can still run without a token.

## Start MongoDB and import the graph

```sh
docker compose up -d mongodb
docker compose run --rm seed
```

If the `mongo:8.0.29-noble` image is already cached but Docker cannot reach its
registry, add `--pull never` to both commands. On the GB10, either allow the
normal image pull or load a `docker save` archive from the external SSD first.

The `seed` service imports `data/repositories.json`, `data/relationships.json`, and
`data/domains.json` into the `ceo_brain` database and creates graph query indexes.

## Verify the graph

```sh
docker compose exec mongodb mongosh --quiet --eval 'db.getSiblingDB("ceo_brain").repositories.countDocuments()'
docker compose exec mongodb mongosh --quiet --eval 'db.getSiblingDB("ceo_brain").relationships.countDocuments()'
```

The graph contains verified relationships and inference relationships. Each relationship
includes source evidence and a confidence level, so consumers must not treat a shared
functional domain as a direct code dependency.
