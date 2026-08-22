"""Read-only project evidence facade and audit API for CEO Brain."""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import PyMongoError


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "ceo-brain-project-graph" / "data"))
DATABASE = os.getenv("MONGODB_DATABASE", "ceo_brain")
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27018")
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]


class AuditRequest(BaseModel):
    claim: str = Field(min_length=8, max_length=4_000)
    transcriptSegmentIds: list[str] = Field(default_factory=list)


class DecisionRequest(BaseModel):
    decision: Literal["approved", "deferred", "investigate"]
    note: str = Field(default="", max_length=1_000)


class ToolQuery(BaseModel):
    query: str = Field(min_length=2, max_length=1_000)
    projectIds: list[str] = Field(default_factory=list)


class AgentWarningRequest(BaseModel):
    claim: str = Field(min_length=8, max_length=4_000)
    warning: str = Field(min_length=12, max_length=2_000)
    confidence: Literal["low", "medium", "high"]
    projectIds: list[str] = Field(min_length=1, max_length=8)
    evidence: list[dict[str, Any]] = Field(default_factory=list, max_length=12)
    recommendedAction: Literal["investigate", "reuse", "defer", "approve"]


def load_json(name: str) -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


class EvidenceStore:
    """Uses MongoDB when available, with JSON fallback for laptop development."""

    def __init__(self) -> None:
        self.fallback = {name: load_json(name) for name in ("projects.json", "emails.json", "project_relationships.json")}
        self.client: MongoClient | None = None
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=800)
            client.admin.command("ping")
            self.client = client
        except PyMongoError:
            self.client = None

    @property
    def db(self):
        return self.client[DATABASE] if self.client else None

    def projects(self) -> list[dict[str, Any]]:
        return list(self.db.projects.find({}, {"_id": 0})) if self.db is not None else self.fallback["projects.json"]

    def emails(self) -> list[dict[str, Any]]:
        return list(self.db.emails.find({}, {"_id": 0})) if self.db is not None else self.fallback["emails.json"]

    def relationships(self) -> list[dict[str, Any]]:
        return list(self.db.project_relationships.find({}, {"_id": 0})) if self.db is not None else self.fallback["project_relationships.json"]

    def save_audit(self, audit: dict[str, Any]) -> None:
        if self.db is not None:
            self.db.audits.replace_one({"auditId": audit["auditId"]}, audit, upsert=True)

    def get_audit(self, audit_id: str) -> dict[str, Any] | None:
        if self.db is None:
            return AUDIT_CACHE.get(audit_id)
        return self.db.audits.find_one({"auditId": audit_id}, {"_id": 0})

    def save_decision(self, decision: dict[str, Any]) -> None:
        if self.db is not None:
            self.db.decisions.replace_one({"auditId": decision["auditId"]}, decision, upsert=True)


def tokens(value: str) -> set[str]:
    stop_words = {
        "and", "are", "build", "for", "from", "have", "into", "need", "our", "project", "that", "the", "their", "this", "was", "will", "with", "you",
    }
    return {word for word in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", value.lower()) if word not in stop_words}


def rank_projects(query: str, projects: list[dict[str, Any]], emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_tokens = tokens(query)
    email_text: dict[str, str] = {}
    for email in emails:
        email_text[email["projectId"]] = email_text.get(email["projectId"], "") + " " + email["subject"] + " " + email["body"]
    scored = []
    for project in projects:
        metadata = " ".join([project["title"], project["summary"], " ".join(project["domains"])]).lower()
        metadata_matches = query_tokens & tokens(metadata)
        email_matches = query_tokens & tokens(email_text.get(project["projectId"], ""))
        # Email-only matches need several terms: generic words in prose must not trigger an audit.
        if len(metadata_matches) >= 2 or len(email_matches) >= 3:
            matches = sorted(metadata_matches | email_matches)
            scored.append({"project": project, "score": len(metadata_matches) * 2 + len(email_matches), "matchedTerms": matches[:12]})
    return sorted(scored, key=lambda item: (-item["score"], item["project"]["projectId"]))[:8]


def graph_for_projects(project_ids: set[str], projects: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, Any]:
    max_nodes, max_edges = 60, 80
    included = set(project_ids)
    frontier = set(project_ids)
    edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    ordered_relationships = sorted(
        relationships,
        key=lambda edge: (edge["source"] != "verified", -edge["confidence"], edge["fromProject"], edge["toProject"]),
    )
    for _ in range(3):
        next_frontier: set[str] = set()
        for edge in ordered_relationships:
            from_id, to_id = edge["fromProject"], edge["toProject"]
            if from_id not in frontier and to_id not in frontier:
                continue
            unknown_nodes = {from_id, to_id} - included - next_frontier
            if unknown_nodes and len(included) + len(next_frontier) + len(unknown_nodes) > max_nodes:
                continue
            edge_key = (from_id, to_id, edge["relationType"])
            if edge_key not in seen_edges and len(edges) < max_edges:
                edges.append(edge)
                seen_edges.add(edge_key)
            next_frontier.update((from_id, to_id))
            if len(edges) >= max_edges:
                break
        next_frontier -= included
        included.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break
    allowed = {project["projectId"]: project for project in projects}
    nodes = [{key: project[key] for key in ("projectId", "title", "summary", "domains", "source", "portfolio")} for project_id, project in allowed.items() if project_id in included]
    return {"nodes": nodes, "edges": edges, "highlightedNodeIds": sorted(project_ids)}


def make_warning(claim: str, ranked: list[dict[str, Any]], emails: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, Any]:
    project_ids = {item["project"]["projectId"] for item in ranked[:3]}
    related_edges = [edge for edge in relationships if edge["fromProject"] in project_ids or edge["toProject"] in project_ids]
    matched_emails = [email for email in emails if email["projectId"] in project_ids and tokens(claim) & tokens(email["subject"] + " " + email["body"])]
    evidence = [
        {"kind": "github", "projectId": item["project"]["projectId"], "url": item["project"]["source"]["url"], "detail": item["project"]["summary"][:280]}
        for item in ranked[:3]
    ]
    evidence.extend({"kind": "email", "projectId": email["projectId"], "emailId": email["id"], "detail": email["subject"]} for email in matched_emails[:4])
    if len(project_ids) >= 2 and related_edges:
        confidence: Literal["low", "medium", "high"] = "high" if matched_emails else "medium"
        warning = f"Potential overlap: this claim connects to {len(project_ids)} active research projects with {len(related_edges)} recorded graph relationships."
        action = "investigate"
    elif project_ids:
        confidence = "low"
        warning = "Relevant research projects exist, but the current evidence does not justify an intervention yet."
        action = "defer"
    else:
        confidence = "low"
        warning = "Insufficient evidence: no related project or email evidence was found for this claim."
        action = "defer"
    return {"warning": warning, "confidence": confidence, "projectIds": sorted(project_ids), "evidence": evidence, "recommendedAction": action, "relationshipCount": len(related_edges)}


STORE = EvidenceStore()
AUDIT_CACHE: dict[str, dict[str, Any]] = {}
app = FastAPI(title="CEO Brain Evidence API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    # Local Vite dev servers work without configuration. Add a deployed Truth
    # Engine URL through CORS_ALLOW_ORIGINS when the UI is not on localhost.
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(?::\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "storage": "mongodb" if STORE.db is not None else "json-fallback", "model": os.getenv("NEMOCLAW_MODEL_ID", "not-configured")}


@app.post("/tools/search-projects")
def search_projects(query: ToolQuery) -> dict[str, Any]:
    matches = rank_projects(query.query, STORE.projects(), STORE.emails())
    return {"matches": [{"projectId": item["project"]["projectId"], "title": item["project"]["title"], "domains": item["project"]["domains"], "score": item["score"], "matchedTerms": item["matchedTerms"]} for item in matches]}


@app.post("/tools/search-emails")
def search_emails(query: ToolQuery) -> dict[str, Any]:
    wanted = set(query.projectIds)
    query_tokens = tokens(query.query)
    results = [email for email in STORE.emails() if (not wanted or email["projectId"] in wanted) and query_tokens & tokens(email["subject"] + " " + email["body"])]
    return {"emails": [{key: email[key] for key in ("id", "projectId", "date", "from", "subject", "body", "labels")} for email in results[:12]]}


@app.post("/tools/get-graph-neighborhood")
def get_graph_neighborhood(query: ToolQuery) -> dict[str, Any]:
    project_ids = set(query.projectIds) or {item["project"]["projectId"] for item in rank_projects(query.query, STORE.projects(), STORE.emails())[:3]}
    return graph_for_projects(project_ids, STORE.projects(), STORE.relationships())


@app.post("/tools/get-github-evidence")
def get_github_evidence(query: ToolQuery) -> dict[str, Any]:
    selected = set(query.projectIds)
    return {"projects": [{"projectId": project["projectId"], "source": project["source"], "summary": project["summary"]} for project in STORE.projects() if project["projectId"] in selected]}


@app.post("/tools/create-audit-warning")
def create_agent_warning(request: AgentWarningRequest) -> dict[str, Any]:
    valid_projects = {project["projectId"] for project in STORE.projects()}
    project_ids = sorted(set(request.projectIds) & valid_projects)
    if not project_ids:
        raise HTTPException(status_code=422, detail="No valid project IDs in agent warning")
    # An agent cannot claim high confidence without multiple citations and project evidence.
    confidence = request.confidence
    if confidence == "high" and (len(project_ids) < 2 or len(request.evidence) < 2):
        confidence = "medium"
    audit = {
        "auditId": str(uuid.uuid4()),
        "claim": request.claim,
        "status": "warning_ready",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "events": ["agent_evidence_received", "warning_schema_validated", "warning_ready"],
        "warning": request.warning,
        "confidence": confidence,
        "projectIds": project_ids,
        "evidence": request.evidence,
        "recommendedAction": request.recommendedAction,
        "relationshipCount": sum(1 for edge in STORE.relationships() if edge["fromProject"] in project_ids or edge["toProject"] in project_ids),
    }
    AUDIT_CACHE[audit["auditId"]] = audit
    STORE.save_audit(audit)
    return audit


@app.post("/audits")
def create_audit(request: AuditRequest) -> dict[str, Any]:
    projects, emails, relationships = STORE.projects(), STORE.emails(), STORE.relationships()
    ranked = rank_projects(request.claim, projects, emails)
    report = make_warning(request.claim, ranked, emails, relationships)
    audit = {"auditId": str(uuid.uuid4()), "claim": request.claim, "transcriptSegmentIds": request.transcriptSegmentIds, "status": "warning_ready", "createdAt": datetime.now(timezone.utc).isoformat(), "events": ["claim_received", "projects_ranked", "graph_queried", "emails_checked", "warning_ready"], **report}
    AUDIT_CACHE[audit["auditId"]] = audit
    STORE.save_audit(audit)
    return audit


@app.get("/audits/{audit_id}/events")
def audit_events(audit_id: str):
    audit = STORE.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    def stream():
        for event in audit["events"]:
            yield f"event: status\\ndata: {json.dumps({'event': event, 'auditId': audit_id})}\\n\\n"
        yield f"event: complete\\ndata: {json.dumps({'auditId': audit_id, 'confidence': audit['confidence']})}\\n\\n"
    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/audits/{audit_id}/graph")
def audit_graph(audit_id: str) -> dict[str, Any]:
    audit = STORE.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    graph = graph_for_projects(set(audit["projectIds"]), STORE.projects(), STORE.relationships())
    return {**graph, "evidence": audit["evidence"]}


@app.post("/audits/{audit_id}/decision")
def create_decision(audit_id: str, request: DecisionRequest) -> dict[str, Any]:
    if not STORE.get_audit(audit_id):
        raise HTTPException(status_code=404, detail="Audit not found")
    decision = {"auditId": audit_id, "decision": request.decision, "note": request.note, "createdAt": datetime.now(timezone.utc).isoformat()}
    STORE.save_decision(decision)
    return decision
