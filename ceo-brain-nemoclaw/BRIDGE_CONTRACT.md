# NemoClaw Audit Bridge Contract

Set `NEMOCLAW_AUDIT_WEBHOOK_URL` on the GB10 API to an operator-managed local
bridge that starts a NemoClaw audit run. The API posts this payload:

```json
{
  "auditId": "uuid",
  "claim": "meeting transcript claim",
  "callbackUrl": "/tools/create-audit-warning"
}
```

The bridge gives the agent the `auditId` and claim in its task prompt. The agent
uses only `tools/ceo_brain_tools.py`, then posts this schema to the callback:

```json
{
  "auditId": "uuid",
  "claim": "meeting transcript claim",
  "warning": "concise grounded intervention",
  "confidence": "low | medium | high",
  "projectIds": ["gr/project-id"],
  "evidence": [{"kind": "github | email", "projectId": "gr/project-id", "detail": "citation"}],
  "recommendedAction": "investigate | reuse | defer | approve"
}
```

The agent calls:

```sh
CEO_BRAIN_API_URL=http://<gb10-api-host>:8080 \
python3 tools/ceo_brain_tools.py create-audit-warning --warning-json /tmp/warning.json
```

The sandbox receives no MongoDB credentials, GitHub write credentials, or
`ground_truth.json`. A successful callback changes the original audit to
`warning_ready`; the UI then enables its graph button.
