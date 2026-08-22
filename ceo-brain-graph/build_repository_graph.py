#!/usr/bin/env python3
"""Build a MongoDB-ready knowledge graph for selected google-research repositories."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ORG = "google-research"
API_ROOT = "https://api.github.com"
RAW_ROOT = "https://raw.githubusercontent.com"
REPOSITORY_LIMIT = 50
DEPENDENCY_FILES = ("requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py", "environment.yml")
COMMON_DEPENDENCIES = {"numpy", "scipy", "pandas", "matplotlib", "pytest", "absl-py", "six", "tqdm"}

DOMAIN_RULES: dict[str, dict[str, Any]] = {
    "messaging_queueing": {"label": "Messaging and Queueing", "keywords": ["queue", "message queue", "pubsub", "pub-sub", "messaging", "event stream"]},
    "notification_alerting": {"label": "Notification and Alerting", "keywords": ["notification", "alert", "alerting", "pager", "reminder"]},
    "search_retrieval": {"label": "Search and Retrieval", "keywords": ["information retrieval", "semantic search", "neural retrieval", "retriever", "search ranking", "document ranking"]},
    "tracking_observability": {"label": "Tracking, Telemetry, and Observability", "keywords": ["telemetry", "observability", "distributed tracing", "monitoring system", "event tracking"]},
    "agent_orchestration": {"label": "Agent Orchestration and Tool Use", "keywords": ["agentic", "tool use", "agent planning", "agent orchestration", "autonomous agent"]},
    "data_pipelines": {"label": "Data Ingestion and Pipelines", "keywords": ["pipeline", "ingestion", "dataflow", "apache beam", "etl", "streaming"]},
    "developer_tooling": {"label": "Developer Tooling and Code Intelligence", "keywords": ["code intelligence", "program synthesis", "compiler", "software engineering", "code completion"]},
    "evaluation": {"label": "Evaluation, Benchmarking, and Testing", "keywords": ["benchmark", "evaluation", "evaluate", "test set", "leaderboard"]},
    "ml_training": {"label": "ML Training and Experiment Management", "keywords": ["training", "train", "optimizer", "tensorflow", "jax", "flax", "pytorch"]},
    "llm_prompting": {"label": "Foundation Models, LLMs, and Prompting", "keywords": ["foundation model", "language model", "large language", "prompting", "generative ai"]},
    "nlp": {"label": "NLP and Document Understanding", "keywords": ["natural language", "machine translation", "question answering", "document understanding", "text classification"]},
    "speech_audio": {"label": "Speech, Audio, and Diarization", "keywords": ["speech", "audio", "asr", "speaker", "diarization", "voice"]},
    "vision_video": {"label": "Vision, Video, and Image Understanding", "keywords": ["vision", "image", "video", "segmentation", "object detection", "camera"]},
    "multimodal": {"label": "Multimodal AI", "keywords": ["multimodal", "vision-language", "image-text", "audio-visual"]},
    "recommendation": {"label": "Recommendation, Ranking, and Personalization", "keywords": ["recommendation", "recommender", "personalization", "ranking"]},
    "forecasting": {"label": "Forecasting and Time Series", "keywords": ["forecast", "time series", "timeseries", "temporal"]},
    "privacy_federated_security": {"label": "Federated Learning, Privacy, and Security", "keywords": ["federated", "privacy", "secure", "security", "differential privacy"]},
    "graph_network": {"label": "Graph Learning and Network Analysis", "keywords": ["graph neural", "graph learning", "network analysis", "knowledge graph"]},
    "optimization": {"label": "Optimization and Decision Systems", "keywords": ["optimization", "optimisation", "decision", "constraint", "routing"]},
    "robotics_spatial": {"label": "Robotics, Spatial Reasoning, and Control", "keywords": ["robot", "robotics", "control", "navigation", "spatial"]},
    "health_bio": {"label": "Healthcare and Bioinformatics", "keywords": ["health", "medical", "clinical", "genomic", "protein", "biomedical"]},
    "climate_geospatial": {"label": "Climate, Geospatial, and Sustainability", "keywords": ["climate", "geospatial", "weather", "earth", "sustainability"]},
    "education_knowledge": {"label": "Education and Knowledge Systems", "keywords": ["education", "learning science", "knowledge", "tutor"]},
    "responsible_ai": {"label": "Responsible AI, Safety, Fairness, and Interpretability", "keywords": ["fairness", "bias", "safety", "responsible", "interpretability", "explainability"]},
}


def request(url: str) -> urllib.request.Request:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ceo-brain-repository-graph"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def fetch_json(url: str) -> Any:
    with urllib.request.urlopen(request(url), timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    try:
        with urllib.request.urlopen(request(url), timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return ""
        raise


def recent_repositories(limit: int) -> list[dict[str, Any]]:
    curated: list[dict[str, Any]] = []
    page = 1
    while len(curated) < limit:
        batch = fetch_json(f"{API_ROOT}/orgs/{ORG}/repos?per_page=100&page={page}&sort=updated&direction=desc")
        if not batch:
            break
        curated.extend(repo for repo in batch if not repo.get("archived") and repo.get("description"))
        page += 1
    return curated[:limit]


def normalize_dependency(value: str) -> str:
    return re.split(r"[<>=!~\[\s]", value.strip().lower(), maxsplit=1)[0].replace("_", "-")


def extract_dependencies(files: dict[str, str]) -> list[str]:
    dependencies: set[str] = set()
    for path, content in files.items():
        if path.endswith(".txt"):
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    dependencies.add(normalize_dependency(line))
        else:
            for package in re.findall(r"(?:tensorflow|jax|flax|torch|pytorch|transformers|apache-beam|ray|tensorflow-federated)", content, re.I):
                dependencies.add(package.lower())
    return sorted(dep for dep in dependencies if dep)


def classify_domains(text: str) -> tuple[list[str], dict[str, list[str]]]:
    normalized = text.lower()
    matched: dict[str, list[str]] = {}
    for domain_id, definition in DOMAIN_RULES.items():
        hits = [keyword for keyword in definition["keywords"] if re.search(rf"(?<!\\w){re.escape(keyword)}(?!\\w)", normalized)]
        if hits:
            matched[domain_id] = hits[:4]
    if not matched:
        matched["ml_training"] = ["default: research repository"]
    return sorted(matched), matched


def related_repo_links(text: str) -> list[str]:
    return sorted(set(re.findall(r"github\.com/google-research/([A-Za-z0-9_.-]+)", text, re.I)))


def resource_tokens(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>\]]+", text)
    tokens = []
    for url in urls:
        if any(marker in url.lower() for marker in ("arxiv.org", "kaggle.com", "huggingface.co", "tensorflow.org/datasets", "github.com/google-research")):
            tokens.append(url.rstrip(".,"))
    return sorted(set(tokens))[:40]


def build_repository(repo: dict[str, Any], scanned_at: str) -> dict[str, Any]:
    full_name = repo["full_name"]
    branch = repo["default_branch"]
    files = {path: fetch_text(f"{RAW_ROOT}/{full_name}/{branch}/{path}") for path in ("README.md", *DEPENDENCY_FILES)}
    readme = files["README.md"]
    # Classify the project statement, not dependency listings and README boilerplate.
    intro = re.sub(r"https?://\\S+", "", readme[:5000])
    intro = re.sub(r"`[^`]+`", "", intro)
    corpus = "\n".join([repo.get("name", ""), repo.get("description") or "", " ".join(repo.get("topics") or []), intro])
    domains, domain_evidence = classify_domains(corpus)
    dependencies = extract_dependencies(files)
    repo_id = full_name.lower()
    return {
        "repoId": repo_id,
        "fullName": full_name,
        "name": repo["name"],
        "url": repo["html_url"],
        "description": repo.get("description") or "",
        "homepage": repo.get("homepage") or "",
        "defaultBranch": branch,
        "language": repo.get("language"),
        "topics": repo.get("topics") or [],
        "license": (repo.get("license") or {}).get("spdx_id"),
        "updatedAt": repo.get("updated_at"),
        "pushedAt": repo.get("pushed_at"),
        "stars": repo.get("stargazers_count", 0),
        "domains": domains,
        "domainEvidence": domain_evidence,
        "dependencies": dependencies,
        "linkedRepositories": [name for name in related_repo_links(readme) if name.lower().removesuffix(".git") != repo["name"].lower()],
        "resources": resource_tokens(readme),
        "evidence": [{"type": "github_readme", "url": f"{repo['html_url']}/blob/{branch}/README.md", "excerpt": readme[:800]}] if readme else [],
        "scannedAt": scanned_at,
    }


def edge(from_repo: str, to_repo: str, relation_type: str, confidence: float, evidence: list[dict[str, str]], source: str) -> dict[str, Any]:
    return {"fromRepo": from_repo, "toRepo": to_repo, "relationType": relation_type, "confidence": confidence, "evidence": evidence, "source": source}


def cap_edges_per_repository(edges: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Keep a graph legible by retaining only the best scored edges at each node."""
    kept: list[dict[str, Any]] = []
    degree: dict[str, int] = defaultdict(int)
    for item in sorted(edges, key=lambda edge: (-edge["confidence"], -len(edge["evidence"]), edge["fromRepo"], edge["toRepo"])):
        if degree[item["fromRepo"]] >= limit or degree[item["toRepo"]] >= limit:
            continue
        kept.append(item)
        degree[item["fromRepo"]] += 1
        degree[item["toRepo"]] += 1
    return kept


def build_relationships(repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {repo["name"].lower(): repo for repo in repositories}
    direct_edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    dependency_edges: list[dict[str, Any]] = []
    capability_edges: list[dict[str, Any]] = []
    for repo in repositories:
        for linked_name in repo["linkedRepositories"]:
            target = by_name.get(linked_name.lower())
            if target and target["repoId"] != repo["repoId"]:
                item = edge(repo["repoId"], target["repoId"], "mentions_or_links_to", 0.95, [{"type": "readme_link", "url": repo["url"], "detail": linked_name}], "verified")
                direct_edges[(item["fromRepo"], item["toRepo"], item["relationType"])] = item

    for index, left in enumerate(repositories):
        for right in repositories[index + 1 :]:
            shared_dependencies = sorted(set(left["dependencies"]) & set(right["dependencies"]) - COMMON_DEPENDENCIES)
            shared_domains = sorted(set(left["domains"]) & set(right["domains"]))
            shared_resources = sorted(set(left["resources"]) & set(right["resources"]))
            if len(shared_dependencies) >= 2:
                dependency_edges.append(edge(left["repoId"], right["repoId"], "shares_dependency", min(0.95, 0.7 + len(shared_dependencies) * 0.05), [{"type": "dependency", "detail": dependency} for dependency in shared_dependencies[:4]], "verified"))
            if shared_resources:
                item = edge(left["repoId"], right["repoId"], "uses_same_dataset_or_model", 0.75, [{"type": "resource", "detail": resource} for resource in shared_resources[:3]], "verified")
                direct_edges[(item["fromRepo"], item["toRepo"], item["relationType"])] = item
            if len(shared_domains) >= 2 or (len(shared_domains) == 1 and (shared_dependencies or shared_resources)):
                capability_edges.append(edge(left["repoId"], right["repoId"], "provides_similar_capability", 0.65, [{"type": "shared_domain", "detail": domain} for domain in shared_domains[:3]], "inferred"))
    relationships = list(direct_edges.values()) + cap_edges_per_repository(dependency_edges, limit=5) + cap_edges_per_repository(capability_edges, limit=3)
    return sorted(relationships, key=lambda item: (item["fromRepo"], item["toRepo"], item["relationType"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MongoDB-ready graph of google-research repositories.")
    parser.add_argument("--limit", type=int, default=REPOSITORY_LIMIT, help="Number of recent non-archived repositories to include.")
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Directory for MongoDB import JSON files.")
    parser.add_argument("--repositories-file", type=Path, help="Reuse an existing repositories.json file and rebuild only graph edges.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.repositories_file:
        repositories = json.loads(args.repositories_file.read_text(encoding="utf-8"))
        print(f"Reusing {len(repositories)} existing repository nodes", file=sys.stderr)
    else:
        scanned_at = datetime.now(timezone.utc).isoformat()
        source_repositories = recent_repositories(args.limit)
        repositories = []
        for position, repo in enumerate(source_repositories, start=1):
            print(f"[{position}/{len(source_repositories)}] {repo['full_name']}", file=sys.stderr)
            repositories.append(build_repository(repo, scanned_at))
    relationships = build_relationships(repositories)
    domains = [{"id": domain_id, **definition} for domain_id, definition in DOMAIN_RULES.items()]
    for filename, content in (("repositories.json", repositories), ("relationships.json", relationships), ("domains.json", domains)):
        (args.output_dir / filename).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(repositories)} repository nodes and {len(relationships)} relationship edges in {args.output_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
