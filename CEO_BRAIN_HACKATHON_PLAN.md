# CEO Brain: MongoDB Repository Knowledge Graph

## Summary

MongoDB is the core repository-relationship graph, not primarily an email store. CEO Brain scans the 50 most recently updated `google-research` repositories, classifies each into functional capability domains, extracts evidence-backed relationships, and renders an interactive graph.

A live meeting claim becomes a graph query: OpenClaw identifies the requested capability, traverses related repositories and dependencies in MongoDB, correlates synthetic emails, and interrupts only when it can show grounded evidence of overlap, reuse, risk, or an existing solution.

## Graph Data Model

Store source-backed graph documents in MongoDB:

- `repositories`: one node per GitHub repository with metadata, README summary, languages, direct dependencies, functional domains, resources, scan time, and GitHub URLs.
- `relationships`: directed edges with `fromRepo`, `toRepo`, `relationType`, `confidence`, `evidence[]`, `source`, and scan time.
- `domains`: curated capability taxonomy and keyword/framework rules used for deterministic classification.
- `emails`: synthetic internal emails linked to repository IDs, domains, project proposals, and overlap claims.
- `meetings`, `transcript_segments`, `agent_runs`, `evidence_bundles`, `reports`, and `decisions`: records of the live intervention workflow.

Every relationship must contain evidence. Relationship types:

- `imports_or_depends_on`: direct package, module, or repository reference found in code or configuration.
- `mentions_or_links_to`: README, documentation, or source link references another repository.
- `shares_dependency`: matching important framework, package, dataset, model, or infrastructure dependency.
- `uses_same_dataset_or_model`: shared dataset, benchmark, checkpoint, or model resource.
- `provides_similar_capability`: overlapping domains plus corroborating README or specification evidence.
- `email_indicates_overlap`: synthetic-email evidence that teams are duplicating or requesting the same capability.
- `candidate_reuse`: an agent recommendation derived from the preceding evidence; never displayed as a verified direct dependency.

Use MongoDB `$graphLookup` with a maximum traversal depth of three to retrieve connected components and dependency paths for a meeting claim. MongoDB supports recursive traversal with `$graphLookup`; apply early filters and indexed fields to keep queries bounded. See the [MongoDB `$graphLookup` documentation](https://www.mongodb.com/docs/manual/reference/operator/aggregation/graphlookup/).

## Functional Domains

Use deterministic rules plus manual review for the 50 selected repositories. A repository may belong to multiple domains.

- Messaging and queueing
- Notification and alerting
- Search and retrieval
- Tracking, telemetry, and observability
- Agent orchestration and tool use
- Data ingestion and pipelines
- Databases, storage, and data management
- Developer tooling and code intelligence
- Evaluation, benchmarking, and testing
- ML training and experiment management
- Foundation models, LLMs, and prompting
- NLP and document understanding
- Speech, audio, and diarization
- Vision, video, and image understanding
- Multimodal AI
- Recommendation, ranking, and personalization
- Forecasting and time series
- Federated learning, privacy, and security
- Graph learning and network analysis
- Optimization and decision systems
- Robotics, spatial reasoning, and control
- Healthcare and bioinformatics
- Climate, geospatial, and sustainability
- Education and knowledge systems
- Responsible AI, safety, fairness, and interpretability

The graph must label these as functional capabilities, not claim that every Google Research project is a deployable internal service. Reuse recommendations must say whether the evidence is a direct dependency, a capability match, or a research implementation that needs adaptation.

## Live Intervention Flow

1. A meeting video plays in Truth Engine and streams its audio to GB10 local transcription.
2. The transcript detector identifies a proposal, such as "build a notification and queue service."
3. OpenClaw maps the claim to candidate domains, then queries MongoDB for:
   - connected repositories and direct dependency paths;
   - repositories with similar capability evidence;
   - matching synthetic-email threads;
   - resources, constraints, and readiness signals.
4. The agent reads the highest-confidence GitHub evidence directly to verify the graph results.
5. It creates a cited `evidence_bundle` and only intervenes when a configurable threshold is met:
   - direct relationship; or
   - at least two independent capability or email sources with high confidence.
6. The UI highlights the connected graph subnetwork, animates the discovered path, displays why the claim overlaps, and presents the CEO decision card.
7. Approval writes the decision, associated graph path, and estimated savings to MongoDB.

## UI and API Changes

- Add an interactive `react-force-graph-2d` graph panel to Truth Engine with domain-colored repository nodes and evidence-colored relationship edges.
- Clicking a node shows README summary, domain labels, dependencies, outgoing/incoming relationships, confidence, and evidence links.
- Clicking a meeting-triggered verdict focuses the graph on the relevant node plus its three-hop connected component.
- Add API endpoints for graph ingest, graph summary, repository detail, bounded path traversal, and meeting-claim analysis.
- Replace generic "Git repo scanner" terminal messages with explicit graph events: `classified`, `edge_discovered`, `path_found`, `email_corroborated`, and `intervention_threshold_met`.
- Preserve live GitHub scanning, but cache normalized nodes and edges in MongoDB. Label all visual evidence as `LIVE`, `CACHED`, or `SYNTHETIC`.

## Test Plan

- Ingest 50 recent repositories and verify every repository has at least one reviewed functional-domain label.
- Verify direct-dependency edges require source-file evidence and URL or path references.
- Verify inferred capability edges are visibly labeled as inferred and never presented as imports.
- Query a known repo with `$graphLookup` and confirm its three-hop graph result is bounded, deduplicated, and evidence-linked.
- Run the Project Titan meeting scenario and verify the UI highlights an evidence path, retrieves relevant synthetic emails, stores the report, and persists approval.
- Run the full scenario with GitHub unavailable and verify MongoDB cached graph data powers the same visual path and report.
- Run a no-match claim and verify CEO Brain reports insufficient evidence instead of inventing an intervention.

## Assumptions

- The hackathon graph covers 50 recent repositories, not the full Google Research organization.
- The primary visualization is an interactive force graph; the graph is part of the main CEO decision flow rather than a hidden admin view.
- Rule-based classification plus review is the source of truth for domain labels; the local model may explain labels but cannot silently change them.
- The GB10 hosts MongoDB, OpenClaw/NemoClaw/OpenShell, transcription, and local LLM inference; the laptop hosts the presentation UI.
