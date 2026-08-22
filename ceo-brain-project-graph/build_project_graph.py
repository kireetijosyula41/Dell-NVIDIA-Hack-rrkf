#!/usr/bin/env python3
"""Generate MongoDB import documents from the synthetic project-email dataset.

This script intentionally never reads ground_truth.json. Ground truth is reserved
for offline evaluation so the runtime agent cannot learn planted answers.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import warnings
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DOMAIN_RULES: dict[str, tuple[str, ...]] = {
    "agent_orchestration": ("agent", "tool use", "planning", "autonomous"),
    "code_intelligence": ("code", "program", "compiler", "software"),
    "evaluation": ("benchmark", "evaluation", "eval", "metric", "leaderboard"),
    "forecasting": ("forecast", "time series", "temporal", "weather"),
    "foundation_models": ("language model", "foundation model", "transformer", "prompt"),
    "generative_media": ("diffusion", "generation", "image", "video", "inpainting"),
    "health_bio": ("protein", "genomic", "medical", "health", "clinical"),
    "multimodal": ("multimodal", "vision-language", "image-text", "audio-visual"),
    "nlp": ("natural language", "translation", "text", "linguistic", "question answering"),
    "optimization": ("optimization", "optimisation", "constraint", "routing"),
    "privacy_federated": ("federated", "privacy", "secure", "fairness", "bias"),
    "recommendation": ("recommendation", "ranking", "personalization"),
    "robotics_control": ("robot", "control", "navigation", "embodied"),
    "search_retrieval": ("retrieval", "search", "retriever", "index"),
    "speech_audio": ("speech", "audio", "voice", "tts", "speaker"),
    "vision": ("vision", "image", "video", "segmentation", "camera"),
}

RESOURCE_PATTERNS = {
    "gpu": re.compile(r"\b(?:H100|A100|GPU|TPU|DGX|Vulcan)\b[^.\n;]*", re.I),
    "service": re.compile(r"\b(?:service|endpoint|platform|backend|pipeline|cluster)\b[^.\n;]*", re.I),
    "dataset": re.compile(r"\b(?:dataset|benchmark|corpus|eval set|test set)\b[^.\n;]*", re.I),
    "person": re.compile(r"\b[A-Z][a-z]+ at \d+%\b"),
}

SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".go", ".rs"}
MANIFEST_NAMES = {"package.json", "pyproject.toml", "setup.py", "setup.cfg", "environment.yml", "environment.yaml", "pom.xml"}
MAX_SOURCE_FILE_BYTES = 1_000_000


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def classify_domains(text: str) -> tuple[list[str], dict[str, list[str]]]:
    lowered = text.lower()
    evidence: dict[str, list[str]] = {}
    for domain, keywords in DOMAIN_RULES.items():
        hits = [keyword for keyword in keywords if keyword in lowered]
        if hits:
            evidence[domain] = hits[:3]
    if not evidence:
        evidence["evaluation"] = ["default: research project"]
    return sorted(evidence), evidence


def extract_resource_claims(email: dict[str, Any]) -> list[dict[str, str]]:
    claims: list[dict[str, str]] = []
    for kind, pattern in RESOURCE_PATTERNS.items():
        for match in pattern.findall(email["body"]):
            value = normalize(match)
            if len(value) >= 8:
                claims.append({"kind": kind, "value": value[:220], "emailId": email["id"]})
    return claims


def normalize_dependency(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value.strip().lower())


def dependency_from_requirement(line: str) -> str | None:
    line = line.split("#", 1)[0].strip()
    if not line or line.startswith(("-", "http:", "https:", "git+")):
        return None
    match = re.match(r"([A-Za-z0-9_.-]+)", line)
    return normalize_dependency(match.group(1)) if match else None


def source_reference_paths(text: str) -> set[str]:
    return {
        match.group(1).strip("/.,)")
        for match in re.finditer(r"google-research/google-research/(?:tree|blob)/(?:master|main)/([^\s#]+)", text)
    }


def scan_python_imports(path: Path) -> set[str]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (OSError, SyntaxError, UnicodeError):
        return set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split(".", 1)[0])
    return modules


def scan_project_source(source_root: Path | None, source_path: str) -> dict[str, Any]:
    if source_root is None:
        return {"available": False, "dependencies": [], "imports": [], "githubReferences": [], "evidence": []}
    project_root = source_root / source_path
    if not project_root.is_dir():
        return {"available": False, "dependencies": [], "imports": [], "githubReferences": [], "evidence": []}
    dependencies: set[str] = set()
    imports: set[str] = set()
    github_references: set[str] = set()
    evidence: list[dict[str, str]] = []
    files_scanned = 0
    for path in project_root.rglob("*"):
        if not path.is_file() or path.stat().st_size > MAX_SOURCE_FILE_BYTES:
            continue
        relative = str(path.relative_to(source_root))
        name = path.name.lower()
        suffix = path.suffix.lower()
        if suffix not in SOURCE_SUFFIXES and name not in MANIFEST_NAMES and not name.startswith("requirements") and not name.startswith("readme"):
            continue
        files_scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        if name.startswith("requirements"):
            found = {dependency_from_requirement(line) for line in text.splitlines()}
            dependencies.update(item for item in found if item)
        elif name == "package.json":
            try:
                package = json.loads(text)
                for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                    dependencies.update(normalize_dependency(item) for item in package.get(key, {}))
            except json.JSONDecodeError:
                pass
        elif name in {"pyproject.toml", "setup.py", "setup.cfg", "environment.yml", "environment.yaml"}:
            dependencies.update(normalize_dependency(match.group(1)) for match in re.finditer(r"[\"']([A-Za-z0-9_.-]+)(?:[<>=!~][^\"']*)?[\"']", text))
        if suffix == ".py":
            imports.update(normalize_dependency(item) for item in scan_python_imports(path) if item not in sys.stdlib_module_names)
        elif suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            imports.update(normalize_dependency(match.group(1).split("/", 1)[0]) for match in re.finditer(r"(?:from\s+|require\()['\"]([^'\"]+)", text))
        references = source_reference_paths(text)
        if references:
            github_references.update(references)
            evidence.extend({"type": "github_source_reference", "file": relative, "detail": reference} for reference in sorted(references)[:3])
    return {
        "available": True,
        "filesScanned": files_scanned,
        "dependencies": sorted(dependencies),
        "imports": sorted(imports),
        "githubReferences": sorted(github_references),
        "evidence": evidence[:30],
    }


def load_dataset(dataset_root: Path, source_root: Path | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    projects: list[dict[str, Any]] = []
    emails: list[dict[str, Any]] = []
    scanned_at = datetime.now(timezone.utc).isoformat()
    for project_file in sorted(dataset_root.glob("*/project.json")):
        raw = json.loads(project_file.read_text(encoding="utf-8"))
        project_dir = project_file.parent
        project_emails = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((project_dir / "emails").glob("*.json"))]
        domains, domain_evidence = classify_domains(" ".join([raw.get("title", ""), raw.get("summary", ""), *[email["body"] for email in project_emails]]))
        claims = [claim for email in project_emails for claim in extract_resource_claims(email)]
        technical = scan_project_source(source_root, raw["source"]["path"])
        projects.append(
            {
                "projectId": raw["id"],
                "title": raw["title"],
                "summary": raw["summary"],
                "portfolio": raw.get("portfolio"),
                "pm": raw.get("pm"),
                "em": raw.get("em"),
                "contributors": raw.get("contributors", []),
                "window": raw.get("window"),
                "source": raw["source"],
                "domains": domains,
                "domainEvidence": domain_evidence,
                "emailIds": [email["id"] for email in project_emails],
                "resourceClaims": claims,
                "dependencies": technical["dependencies"],
                "imports": technical["imports"],
                "githubReferences": technical["githubReferences"],
                "sourceScan": {key: value for key, value in technical.items() if key not in {"dependencies", "imports", "githubReferences"}},
                "synthetic": True,
                "scannedAt": scanned_at,
            }
        )
        for email in project_emails:
            emails.append({**email, "projectId": raw["id"], "synthetic": True})
    return projects, emails


def relationship(from_id: str, to_id: str, relation_type: str, confidence: float, evidence: list[dict[str, str]], source: str) -> dict[str, Any]:
    return {"fromProject": from_id, "toProject": to_id, "relationType": relation_type, "confidence": confidence, "evidence": evidence, "source": source}


def cap_edges(edges: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    degree: dict[str, int] = defaultdict(int)
    kept: list[dict[str, Any]] = []
    for item in sorted(edges, key=lambda edge: (-edge["confidence"], -len(edge["evidence"]), edge["fromProject"], edge["toProject"])):
        if degree[item["fromProject"]] >= limit or degree[item["toProject"]] >= limit:
            continue
        kept.append(item)
        degree[item["fromProject"]] += 1
        degree[item["toProject"]] += 1
    return kept


def merge_relationships(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one indexed edge per pair/type while retaining its distinct evidence."""
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for edge in edges:
        key = (edge["fromProject"], edge["toProject"], edge["relationType"])
        current = merged.get(key)
        if current is None:
            merged[key] = {**edge, "evidence": list(edge["evidence"])}
            continue
        current["confidence"] = max(current["confidence"], edge["confidence"])
        if edge["source"] == "verified":
            current["source"] = "verified"
        known = {(item.get("type"), item.get("detail"), item.get("emailId")) for item in current["evidence"]}
        for item in edge["evidence"]:
            item_key = (item.get("type"), item.get("detail"), item.get("emailId"))
            if item_key not in known and len(current["evidence"]) < 12:
                current["evidence"].append(item)
                known.add(item_key)
    return list(merged.values())


def build_technical_relationships(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    path_to_project = {project["source"]["path"].strip("/"): project["projectId"] for project in projects}
    module_to_project = {normalize_dependency(path.split("/")[-1]): project_id for path, project_id in path_to_project.items()}
    direct_edges: list[dict[str, Any]] = []
    dependency_owners: dict[str, list[dict[str, Any]]] = defaultdict(list)
    import_owners: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for project in projects:
        project_id = project["projectId"]
        for module in project["imports"]:
            target = module_to_project.get(module)
            if target and target != project_id:
                direct_edges.append(relationship(project_id, target, "local_project_import", 0.96, [{"type": "source_import", "detail": module}], "verified"))
            import_owners[module].append(project)
        for reference in project["githubReferences"]:
            target = path_to_project.get(reference.split("/", 1)[0])
            if target and target != project_id:
                direct_edges.append(relationship(project_id, target, "github_source_reference", 0.92, [{"type": "github_source_reference", "detail": reference}], "verified"))
        for dependency in project["dependencies"]:
            dependency_owners[dependency].append(project)

    def shared_edges(groups: dict[str, list[dict[str, Any]]], relation_type: str, evidence_type: str, confidence: float) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item, owners in groups.items():
            if not 2 <= len(owners) <= 24:
                continue
            for index, left in enumerate(owners):
                for right in owners[index + 1 :]:
                    result.append(relationship(left["projectId"], right["projectId"], relation_type, confidence, [{"type": evidence_type, "detail": item}], "verified"))
        return cap_edges(result, 10)

    return sorted(
        cap_edges(direct_edges, 8)
        + shared_edges(dependency_owners, "shared_declared_dependency", "declared_dependency", 0.86)
        + shared_edges(import_owners, "shared_source_import", "source_import", 0.78),
        key=lambda edge: (edge["fromProject"], edge["toProject"], edge["relationType"]),
    )


def build_relationships(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domain_edges: list[dict[str, Any]] = []
    resource_edges: list[dict[str, Any]] = []
    for index, left in enumerate(projects):
        for right in projects[index + 1 :]:
            shared_domains = sorted(set(left["domains"]) & set(right["domains"]))
            if len(shared_domains) >= 2:
                domain_edges.append(relationship(left["projectId"], right["projectId"], "shared_functional_domain", 0.64, [{"type": "domain", "detail": domain} for domain in shared_domains[:3]], "inferred"))
            left_claims = {(claim["kind"], claim["value"].lower()): claim for claim in left["resourceClaims"]}
            right_claims = {(claim["kind"], claim["value"].lower()): claim for claim in right["resourceClaims"]}
            shared_claims = sorted(set(left_claims) & set(right_claims))
            if shared_claims:
                evidence = []
                for key in shared_claims[:2]:
                    evidence.extend([
                        {"type": "email_resource_claim", "detail": left_claims[key]["value"], "emailId": left_claims[key]["emailId"]},
                        {"type": "email_resource_claim", "detail": right_claims[key]["value"], "emailId": right_claims[key]["emailId"]},
                    ])
                resource_edges.append(relationship(left["projectId"], right["projectId"], "matching_resource_claim", 0.82, evidence, "verified"))
    return sorted(
        merge_relationships(cap_edges(resource_edges, 4) + cap_edges(domain_edges, 3) + build_technical_relationships(projects)),
        key=lambda edge: (edge["fromProject"], edge["toProject"], edge["relationType"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build MongoDB import files for CEO Brain project evidence graph.")
    parser.add_argument("--dataset-root", type=Path, default=Path("datasets/google-research/projects"))
    parser.add_argument("--source-root", type=Path, help="Local checkout of google-research/google-research. Technical dependency extraction is skipped when omitted.")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_root = args.source_root.resolve() if args.source_root and args.source_root.is_dir() else None
    if args.source_root and source_root is None:
        parser.error(f"--source-root does not exist or is not a directory: {args.source_root}")
    projects, emails = load_dataset(args.dataset_root, source_root)
    relationships = build_relationships(projects)
    domains = [{"id": domain, "keywords": list(keywords)} for domain, keywords in DOMAIN_RULES.items()]
    for name, content in (("projects.json", projects), ("emails.json", emails), ("project_relationships.json", relationships), ("project_domains.json", domains)):
        (args.output_dir / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(projects)} projects, {len(emails)} emails, and {len(relationships)} relationships.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
