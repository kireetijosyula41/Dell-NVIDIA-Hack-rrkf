# PM-Slop Corpus — synthetic stakeholder emails over real repositories

A benchmark-quality synthetic dataset for agents that reason **across** an
organization's projects, not just within one. Real repositories provide the
technical substance; a fictional company ("Meridian Research") provides the
organizational layer: PMs, EMs, engineers, GPU quotas, budget lines, launch
reviews — and 3–4 stakeholder emails per project.

The corpus is engineered to demonstrate **PM slop**: when 320 products are built
simultaneously, every email thread is locally coherent, but the org is quietly
double-booking clusters, duplicating tooling work, overcommitting the same
engineers, and quoting four different dates for the same platform freeze. Nobody
in any single thread can see it. An agent with the whole corpus can — and can be
**scored exactly**, because every contradiction was planted deterministically and
is recorded in ground-truth files.

## Contents

- `datasets/google-research/` — 320 projects from the
  [google-research/google-research](https://github.com/google-research/google-research)
  monorepo (Apache-2.0), each with `project.json`, 3–4 `emails/*.json`, and
  `ground_truth.json`.
- `company/` — the shared fiction: cast of 64 personas, shared infrastructure,
  portfolio assignments, and `conflict_map.json` (the complete list of planted
  cross-project conflicts).
- `docs/DATASET_SPEC.md` — schemas and layout. `docs/PM_SLOP.md` — the conflict
  taxonomy and how to evaluate a detector against ground truth.
- `prompts/` + `scripts/` + `batches/` — the full reproducible pipeline
  (fetch → plan → generate → validate → commit), reusable for other companies'
  repos.

## Quick start for agents

```bash
python3 scripts/validate.py            # integrity check + corpus stats
jq '.conflicts[0]' company/conflict_map.json   # what a planted conflict looks like
cat datasets/google-research/projects/*/emails/e02.json | head   # where claims usually land
```

Everything under `@meridian.example` is fictional. `synthetic: true` on every
project. Source attribution and license in each `project.json.source`.
