# Dataset specification

One dataset = one real company/org's repositories + a synthetic communication layer
on top of them. This repo currently ships `datasets/google-research/`; the layout is
designed so more companies can be added the same way.

## Layout

```
company/                          # the fictional operating company (shared across the dataset)
  company.json                    # name, domain, fiction statement, source attribution
  personas.json                   # the full cast: leadership, pms, ems, engineers, functions
  resources.json                  # shared GPU clusters, platform teams, processes, canonical facts
  portfolios.json                 # project -> portfolio/PM/EM/contributors/window assignment
  conflict_map.json               # ALL planted cross-project conflicts (global ground truth)
batches/batch-NN.json             # self-contained generation work orders (16 projects each)
prompts/email-generation.md       # the subagent prompt that turns a batch into emails
scripts/                          # fetch -> plan -> generate -> validate -> commit pipeline
datasets/google-research/
  manifest.json                   # index of all projects + corpus stats
  projects/<dir>/
    project.json                  # project metadata + source attribution
    ground_truth.json             # which conflicts were planted in which emails
    emails/e01.json .. e0N.json   # 3-4 emails, chronological
```

## Email schema

See `prompts/email-generation.md` for the authoritative field list. Summary:
`id`, `thread_id`, `in_reply_to`, `date` (ISO-8601 UTC, strictly increasing per
thread), `from`/`to`/`cc` (objects with `name`, `email`, `role` — must exist in
`personas.json`), `subject`, `body` (plain text, 80-200 words), `labels`.

## Ground truth model

PM-slop is planted centrally, before generation, in `company/conflict_map.json`.
Each conflict has an `id`, a `type`, the participating `projects`, the
`shared_object` being contended, `canonical` facts, and a `per_project` claim.
Generators plant their project's claim without referencing the counterpart; each
project's `ground_truth.json` records where the claim landed. Evaluation of a
"slop-detection" agent is therefore exact: join emails across projects on
`shared_object` details and compare against `conflict_map.json`.

## Conflict taxonomy

| type | what's contradictory |
|---|---|
| `gpu_double_booking` | two projects each believe they hold the same cluster reservation for the same week |
| `duplicate_effort` | two teams independently staff building the same internal artifact |
| `shared_person_overcommit` | one engineer committed >=60% to two projects for the same month |
| `codename_collision` | two unrelated efforts use the same internal codename |
| `dependency_date_drift` | four projects quote different dates for the same platform freeze (one is right) |
| `budget_overallocation` | the same finance budget line is verbally promised to two projects |

## Provenance & licensing

Real technical grounding comes from `google-research/google-research` (Apache-2.0);
each `project.json.source` links the exact subdirectory. Every person, email
address (`@meridian.example`, an RFC-2606-reserved domain), date, budget and
decision is fictional; `"synthetic": true` is stamped on every project.

## Adding another company

1. Point `scripts/fetch_readmes.sh` at the new org/monorepo.
2. Re-run `scripts/plan_dataset.py` with a new seed and output under a new
   `datasets/<company>/` root (adjust company fiction/personas as desired).
3. Fan out `prompts/email-generation.md` over the generated batches.
4. `scripts/validate.py` then `scripts/commit_and_push.sh`.
