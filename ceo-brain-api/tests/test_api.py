import asyncio
import unittest
from pathlib import Path

from app.main import AgentWarningRequest, AuditRequest, DecisionRequest, STORE, ToolQuery, app, audit_graph, create_agent_warning, create_audit, create_decision, search_projects


class EvidenceApiTests(unittest.TestCase):
    def test_laptop_ui_origin_can_call_gb10_api(self):
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        asyncio.run(
            app(
                {
                    "type": "http",
                    "asgi": {"version": "3.0"},
                    "http_version": "1.1",
                    "method": "OPTIONS",
                    "scheme": "http",
                    "path": "/audits",
                    "raw_path": b"/audits",
                    "query_string": b"",
                    "headers": [
                        (b"origin", b"http://localhost:5173"),
                        (b"access-control-request-method", b"POST"),
                    ],
                    "client": ("127.0.0.1", 50000),
                    "server": ("127.0.0.1", 8080),
                },
                receive,
                send,
            )
        )
        start = next(message for message in messages if message["type"] == "http.response.start")
        headers = {key.decode(): value.decode() for key, value in start["headers"]}
        self.assertEqual(start["status"], 200)
        self.assertEqual(headers["access-control-allow-origin"], "http://localhost:5173")

    def test_runtime_dataset_is_loaded_without_ground_truth(self):
        self.assertEqual(len(STORE.projects()), 320)
        self.assertEqual(len(STORE.emails()), 1257)
        runtime_root = Path(__file__).resolve().parents[2] / "ceo-brain-project-graph" / "data"
        self.assertFalse(any(path.name == "ground_truth.json" for path in runtime_root.rglob("*.json")))

    def test_emails_and_relationships_reference_known_projects(self):
        project_ids = {project["projectId"] for project in STORE.projects()}
        self.assertTrue(all(email["projectId"] in project_ids for email in STORE.emails()))
        self.assertTrue(all(edge["fromProject"] in project_ids and edge["toProject"] in project_ids for edge in STORE.relationships()))
        self.assertTrue(all(edge["evidence"] and edge["source"] in {"verified", "inferred"} for edge in STORE.relationships()))

    def test_audit_graph_is_bounded(self):
        audit = create_audit(AuditRequest(claim="We need a benchmark leaderboard and GPU evaluation pipeline."))
        graph = audit_graph(audit["auditId"])
        self.assertLessEqual(len(graph["nodes"]), 60)
        self.assertLessEqual(len(graph["edges"]), 80)
        self.assertTrue(audit["projectIds"])

    def test_unknown_claim_does_not_invent_intervention(self):
        audit = create_audit(AuditRequest(claim="Replace the office coffee machine with a silent espresso grinder."))
        self.assertEqual(audit["confidence"], "low")
        self.assertEqual(audit["recommendedAction"], "defer")

    def test_project_search_returns_source_backed_project_ids(self):
        result = search_projects(ToolQuery(query="time series forecasting"))
        self.assertTrue(result["matches"])
        self.assertTrue(all(item["projectId"].startswith("gr/") for item in result["matches"]))

    def test_agent_warning_requires_support_for_high_confidence(self):
        audit = create_agent_warning(
            AgentWarningRequest(
                claim="A project team requests a duplicate benchmark service.",
                warning="A potentially overlapping project needs human review.",
                confidence="high",
                projectIds=["gr/CoDi"],
                evidence=[{"kind": "github", "detail": "source link"}],
                recommendedAction="investigate",
            )
        )
        self.assertEqual(audit["confidence"], "medium")

    def test_decision_is_accepted_for_existing_audit(self):
        audit = create_audit(AuditRequest(claim="We need time series forecasting and evaluation benchmarks."))
        decision = create_decision(audit["auditId"], DecisionRequest(decision="investigate", note="test decision"))
        self.assertEqual(decision["auditId"], audit["auditId"])
        self.assertEqual(decision["decision"], "investigate")
        if STORE.db is not None:
            stored = STORE.db.decisions.find_one({"auditId": audit["auditId"]})
            self.assertIsNotNone(stored)


if __name__ == "__main__":
    unittest.main()
