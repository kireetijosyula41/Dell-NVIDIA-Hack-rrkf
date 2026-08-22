import unittest

from app.main import AgentWarningRequest, AuditRequest, STORE, ToolQuery, audit_graph, create_agent_warning, create_audit, search_projects


class EvidenceApiTests(unittest.TestCase):
    def test_runtime_dataset_is_loaded_without_ground_truth(self):
        self.assertEqual(len(STORE.projects()), 320)
        self.assertEqual(len(STORE.emails()), 1257)

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


if __name__ == "__main__":
    unittest.main()
