# PM Slop — what this dataset demonstrates

**The scenario**: Meridian Research runs 320 simultaneous projects with 10 PMs,
8 EMs and 36 engineers. Every conversation is locally coherent — the PM sounds
organized, the dates sound firm, the resourcing sounds settled. The dysfunction
only becomes visible *across* mailboxes: nobody in any single thread has the
context of the other 319 projects.

**Why it's realistic**: none of the planted conflicts require anyone to be wrong
in their own frame. A PM who says "we have Vulcan for the week of June 15" was
told exactly that. The collision exists only in the aggregate — which is precisely
the failure mode of multi-product organizations, and precisely what an agent with
cross-corpus context can catch and a human skimming one inbox cannot.

**What an agent should be able to do with this corpus**:

1. **Detect** — join emails across projects on shared objects (cluster+week,
   person+month, budget line, codename, freeze date) and surface contradictions.
2. **Attribute** — identify which projects/PMs/portfolios are involved and who the
   canonical owner of the contended resource is (`resources.json`).
3. **Adjudicate** — for `dependency_date_drift`, exactly one project quotes the
   true date (`resources.json.canonical_facts`); the agent should say which.
4. **Quantify** — score against ground truth: `company/conflict_map.json` is the
   complete list of planted conflicts; each project's `ground_truth.json` pins the
   exact emails carrying each claim. Precision/recall are directly computable.

**What is noise by design**: most email content (milestones, eval numbers, scope
cuts, technical risks) is conflict-free filler grounded in the real README of each
project. A detector that flags everything scores badly.
