#!/usr/bin/env python3
"""Generate MongoDB import documents from the synthetic project-email dataset.

This script intentionally never reads ground_truth.json. Ground truth is reserved
for offline evaluation so the runtime agent cannot learn planted answers.
"""

from __future__ import annotations

import argparse
import json
import re
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


def load_dataset(dataset_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    projects: list[dict[str, Any]] = []
    emails: list[dict[str, Any]] = []
    scanned_at = datetime.now(timezone.utc).isoformat()
    for project_file in sorted(dataset_root.glob("*/project.json")):
        raw = json.loads(project_file.read_text(encoding="utf-8"))
        project_dir = project_file.parent
        project_emails = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((project_dir / "emails").glob("*.json"))]
        domains, domain_evidence = classify_domains(" ".join([raw.get("title", ""), raw.get("summary", ""), *[email["body"] for email in project_emails]]))
        claims = [claim for email in project_emails for claim in extract_resource_claims(email)]
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
    return sorted(cap_edges(resource_edges, 4) + cap_edges(domain_edges, 3), key=lambda edge: (edge["fromProject"], edge["toProject"], edge["relationType"]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build MongoDB import files for CEO Brain project evidence graph.")
    parser.add_argument("--dataset-root", type=Path, default=Path("datasets/google-research/projects"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    projects, emails = load_dataset(args.dataset_root)
    relationships = build_relationships(projects)
    domains = [{"id": domain, "keywords": list(keywords)} for domain, keywords in DOMAIN_RULES.items()]
    for name, content in (("projects.json", projects), ("emails.json", emails), ("project_relationships.json", relationships), ("project_domains.json", domains)):
        (args.output_dir / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(projects)} projects, {len(emails)} emails, and {len(relationships)} relationships.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
