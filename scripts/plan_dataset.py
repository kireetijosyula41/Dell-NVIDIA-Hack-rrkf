#!/usr/bin/env python3
"""Deterministic dataset planner for the synthetic-email corpus.

Reads the cached READMEs of google-research/google-research projects and emits:
  company/company.json      - the fictional operating company
  company/personas.json     - shared cast of PMs/EMs/engineers/leads
  company/resources.json    - shared clusters, platform teams, processes
  company/portfolios.json   - project -> portfolio/PM/EM/contributor assignment
  company/conflict_map.json - planted cross-project conflicts (PM-slop ground truth)
  batches/batch-NN.json     - self-contained work orders for generation subagents

Everything is seeded so re-running produces identical output. The conflict map is
computed centrally BEFORE any email is written, so independently-generated email
sets for two different projects contradict each other in controlled, verifiable
ways -- which is the whole point of the dataset.

Usage: plan_dataset.py --readmes <dir-of-<project>.md> --out <repo-root>
"""

import argparse
import json
import random
import re
from datetime import date, timedelta
from pathlib import Path

SEED = 20260822
N_PROJECTS = 320
BATCH_SIZE = 16
MIN_README_BYTES = 1000
DOMAIN = "meridian.example"
SOURCE_ORG = "google-research"
SOURCE_REPO = "google-research"

FIRST = [
    "Amara", "Bilal", "Carmen", "Dmitri", "Efe", "Farah", "Gustavo", "Hana",
    "Idris", "Jun", "Katya", "Leilani", "Mateo", "Nadia", "Oyin", "Priya",
    "Quentin", "Rosa", "Santiago", "Tereza", "Umar", "Vera", "Wanjiru", "Ximena",
    "Yusuf", "Zofia", "Anders", "Bao", "Chiara", "Deshawn", "Eleni", "Fumiko",
    "Giannis", "Halima", "Ivo", "Jelena", "Kofi", "Lucia", "Maren", "Nikhil",
    "Ondrej", "Paloma", "Rafael", "Saoirse", "Tomas", "Ulla", "Viktor", "Wei",
    "Yara", "Zeke", "Alina", "Bruno", "Csilla", "Daniela", "Emeka", "Freya",
    "Goran", "Hyun", "Ines", "Jorge", "Kaia", "Linnea", "Milan", "Noor",
]
LAST = [
    "Okafor", "Novak", "Reyes", "Tanaka", "Lindqvist", "Haddad", "Moreau",
    "Petrov", "Osei", "Varga", "Silva", "Nakamura", "Kowalski", "Rahman",
    "Iversen", "Delgado", "Farkas", "Mensah", "Vukovic", "Aliyev", "Costa",
    "Egede", "Horvat", "Jansen", "Keita", "Lombardi", "Marino", "Ndiaye",
    "Olsen", "Pavic", "Quispe", "Rossi", "Sato", "Toure", "Umeh", "Vasquez",
    "Weber", "Yilmaz", "Zhou", "Abebe", "Bergstrom", "Castillo", "Duran",
    "Eriksen", "Fofana", "Gruber", "Hussain", "Ivanov", "Jokic", "Karlsen",
    "Larsen", "Mbeki", "Nassar", "Oduya", "Pinto", "Ruiz", "Sokolov",
    "Traore", "Uzun", "Vidal", "Wolde", "Yamada", "Zapata", "Andrade",
]

PORTFOLIOS = [
    ("language", "Language & Dialogue", ["nlp", "language", "bert", "text", "translat", "summar", "question", "dialog", "llm", "token", "word", "sentence", "reading"]),
    ("vision", "Vision & Perception", ["vision", "image", "video", "visual", "segment", "detect", "3d", "render", "pixel", "depth", "scene"]),
    ("speech-audio", "Speech & Audio", ["speech", "audio", "sound", "music", "asr", "acoustic", "voice"]),
    ("agents-rl", "Agents & Robotics", ["reinforcement", " rl ", "agent", "robot", "control", "policy", "navigation", "game"]),
    ("health-science", "Health & Science", ["health", "medical", "bio", "protein", "chem", "molecul", "clinical", "genom", "drug", "cell", "weather", "climate"]),
    ("graphs-retrieval", "Graphs, Retrieval & RecSys", ["graph", "cluster", "embedding", "recommend", "retriev", "ranking", "search", "similarity", "nearest"]),
    ("efficiency", "Model Efficiency", ["efficient", "distill", "prun", "quant", "sparse", "compress", "scal", "fast", "latency", "memory"]),
    ("trust-theory", "Trust, Theory & Optimization", ["theor", "optimiz", "bandit", "convex", "privacy", "fairness", "causal", "robust", "uncertain", "federated", "differential"]),
    ("data-platforms", "Datasets & Platforms", ["dataset", "benchmark", "library", "tool", "framework", "code", "corpus", "annotation", "simulation"]),
    ("frontier", "Frontier Bets", []),
]

CODENAMES = [
    "Nimbus", "Basalt", "Sirocco", "Kestrel", "Obsidian", "Meltwater",
    "Palisade", "Quillon", "Riverbed", "Saffron", "Tundra", "Vantage",
]

GLOBAL_WINDOW_START = date(2026, 2, 2)


def load_projects(readme_dir: Path):
    projects = []
    for f in sorted(readme_dir.glob("*.md")):
        raw = f.read_bytes()
        if len(raw) < MIN_README_BYTES:
            continue
        text = raw.decode("utf-8", errors="replace")
        projects.append((f.stem, clean_excerpt(text)))
    return projects[:N_PROJECTS]


def clean_excerpt(text: str, max_chars: int = 1600) -> str:
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("<img", "<p", "</p", "[![", "![")) or "shields.io" in s:
            continue
        s = re.sub(r"<[^>]+>", "", s)
        lines.append(s)
    out = "\n".join(lines).strip()
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out[:max_chars]


def title_from(dirname: str, excerpt: str) -> str:
    for line in excerpt.splitlines():
        s = line.strip().lstrip("#").strip()
        if len(s) >= 8 and not s.lower().startswith(("this ", "code for", "source", "http")):
            return s[:90]
    return dirname.replace("_", " ").replace("-", " ").title()[:90]


def build_personas(rng: random.Random):
    names = [f"{a} {b}" for a, b in zip(FIRST, LAST)]
    rng.shuffle(names)
    it = iter(names)

    def person(role, team, seniority):
        name = next(it)
        handle = name.lower().replace(" ", ".")
        return {
            "name": name,
            "email": f"{handle}@{DOMAIN}",
            "role": role,
            "team": team,
            "seniority": seniority,
        }

    personas = {
        "leadership": [
            person("VP Research", "Office of the VP", "vp"),
            person("Director, Applied Research", "Office of the VP", "director"),
            person("Director, Foundational Research", "Office of the VP", "director"),
        ],
        "pms": [person("Product Manager", pid, "senior") for pid, _, _ in PORTFOLIOS],
        "ems": [person("Engineering Manager", "Engineering", "senior") for _ in range(8)],
        "engineers": [
            person(rng.choice(["Research Engineer", "Research Scientist", "Software Engineer"]), "Engineering", rng.choice(["mid", "senior", "staff"]))
            for _ in range(36)
        ],
        "functions": [
            person("Infrastructure Lead", "Compute Infrastructure", "staff"),
            person("Data Platform Lead", "Corpus Platform", "staff"),
            person("Evaluation Lead", "Evalline", "staff"),
            person("Serving Lead", "Shipyard", "staff"),
            person("Privacy Counsel", "Legal", "senior"),
            person("Finance Partner", "Finance", "senior"),
            person("Program Manager, Launch Review", "PMO", "senior"),
        ],
    }
    return personas


def resources():
    return {
        "gpu_clusters": [
            {"id": "titan-a100", "name": "Titan (A100 pool)", "capacity": "2048 GPUs, shared, best-effort"},
            {"id": "vulcan-h100", "name": "Vulcan (H100 pool)", "capacity": "1024 GPUs, reservation required via Infra Lead"},
            {"id": "cirrus-tpu", "name": "Cirrus (TPU v5 pod)", "capacity": "quarterly allocation per portfolio"},
        ],
        "platform_teams": [
            {"id": "corpus", "name": "Corpus", "what": "data ingestion/labeling platform; v2 migration in flight"},
            {"id": "evalline", "name": "Evalline", "what": "shared evaluation & benchmark harness"},
            {"id": "shipyard", "name": "Shipyard", "what": "model serving & demo deployment"},
        ],
        "processes": [
            {"id": "lrb", "name": "Launch Review Board", "cadence": "biweekly; sign-off required before external demo"},
            {"id": "privacy", "name": "Privacy Review", "cadence": "2-3 week SLA"},
            {"id": "q3-okrs", "name": "Q3 OKR planning", "cadence": "locked 2026-06-26"},
        ],
        "canonical_facts": {
            "corpus_v2_freeze": "2026-07-10",
            "q3_okr_lock": "2026-06-26",
            "vulcan_maintenance": "2026-06-22 to 2026-06-24",
        },
    }


def assign_portfolio(dirname: str, excerpt: str) -> str:
    hay = f" {dirname.lower().replace('_', ' ')} {excerpt.lower()} "
    best, best_hits = "frontier", 0
    for pid, _, kws in PORTFOLIOS:
        hits = sum(hay.count(kw) for kw in kws)
        if hits > best_hits:
            best, best_hits = pid, hits
    return best


def project_window(rng: random.Random):
    start = GLOBAL_WINDOW_START + timedelta(weeks=rng.randint(0, 12))
    end = start + timedelta(weeks=rng.randint(10, 16))
    return start, end


def build_conflicts(rng: random.Random, projs, contributors_of):
    """Assign every project to at least one cross-project conflict group."""
    order = [p["dir"] for p in projs]
    rng.shuffle(order)
    by_dir = {p["dir"]: p for p in projs}
    conflicts = []
    i, cid = 0, 0

    def next_pair():
        nonlocal i
        pair = order[i], order[i + 1]
        i += 2
        return pair

    type_cycle = [
        "gpu_double_booking", "duplicate_effort", "shared_person_overcommit",
        "gpu_double_booking", "duplicate_effort", "dependency_date_drift",
        "shared_person_overcommit", "codename_collision", "budget_overallocation",
    ]
    t = 0
    codename_i = 0
    while i + 1 < len(order):
        ctype = type_cycle[t % len(type_cycle)]
        t += 1
        cid += 1
        conflict_id = f"C{cid:03d}"

        if ctype == "dependency_date_drift":
            group = order[i:i + 4]
            i += len(group)
            wrong_dates = ["2026-06-26", "2026-07-10", "2026-07-24", "2026-08-07"]
            rng.shuffle(wrong_dates)
            conflicts.append({
                "id": conflict_id, "type": ctype, "projects": group,
                "shared_object": "Corpus v2 migration freeze",
                "canonical": {"true_date": "2026-07-10", "owner": "Data Platform Lead"},
                "per_project": {
                    p: {"claim": f"Team plans around a Corpus v2 freeze date of {wrong_dates[k]}."}
                    for k, p in enumerate(group)
                },
            })
            continue

        a, b = next_pair()
        if ctype == "gpu_double_booking":
            cluster = rng.choice(["vulcan-h100", "cirrus-tpu"])
            week = date(2026, 6, 1) + timedelta(weeks=rng.randint(0, 5))
            gpus = rng.choice([128, 256, 384, 512])
            details = {
                "shared_object": f"{cluster} reservation, week of {week.isoformat()}",
                "canonical": {"cluster": cluster, "week_of": week.isoformat(), "capacity_requested_each": gpus},
                "per_project": {
                    a: {"claim": f"Believes it holds the {cluster} reservation ({gpus} accelerators) for the week of {week.isoformat()}."},
                    b: {"claim": f"Also believes it holds the {cluster} reservation ({gpus} accelerators) for the week of {week.isoformat()}."},
                },
            }
            for d in (a, b):
                w = by_dir[d]
                if date.fromisoformat(w["window"]["end"]) < week + timedelta(weeks=2):
                    w["window"]["end"] = (week + timedelta(weeks=2)).isoformat()
        elif ctype == "duplicate_effort":
            artifact = rng.choice([
                "an internal evaluation harness", "a dataset de-duplication pipeline",
                "a distillation training recipe", "a human-rating annotation UI",
                "a benchmark leaderboard service", "a synthetic-data generation pipeline",
            ])
            details = {
                "shared_object": artifact,
                "canonical": {"note": "Both teams are independently building the same thing; neither email thread mentions the other project."},
                "per_project": {
                    a: {"claim": f"Team scopes and staffs building {artifact} from scratch."},
                    b: {"claim": f"Team scopes and staffs building {artifact} from scratch."},
                },
            }
        elif ctype == "shared_person_overcommit":
            eng = rng.choice(contributors_of[a])
            if eng not in contributors_of[b]:
                contributors_of[b].append(eng)
            month = rng.choice(["May", "June", "July"])
            details = {
                "shared_object": f"{eng} at >=60% allocation",
                "canonical": {"person": eng, "month": month},
                "per_project": {
                    a: {"claim": f"{eng} is committed at 60%+ to this project for {month} 2026."},
                    b: {"claim": f"{eng} is committed at 60%+ to this project for {month} 2026."},
                },
            }
        elif ctype == "codename_collision":
            codename = f"Project {CODENAMES[codename_i % len(CODENAMES)]}"
            codename_i += 1
            details = {
                "shared_object": codename,
                "canonical": {"codename": codename},
                "per_project": {
                    a: {"claim": f"Team refers to this effort internally as {codename}."},
                    b: {"claim": f"Team refers to this (different) effort internally as {codename}."},
                },
            }
            by_dir[a]["codename"] = codename
            by_dir[b]["codename"] = codename
        else:  # budget_overallocation
            line = f"Q3 discretionary compute budget line B-{rng.randint(11, 89)}"
            amt = rng.choice(["$120k", "$180k", "$240k"])
            details = {
                "shared_object": line,
                "canonical": {"line": line, "available": amt},
                "per_project": {
                    a: {"claim": f"Finance partner verbally earmarked {amt} from {line} for this project."},
                    b: {"claim": f"Finance partner verbally earmarked the same {amt} from {line} for this project."},
                },
            }
        conflicts.append({"id": conflict_id, "type": ctype, "projects": [a, b], **details})
    return conflicts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--readmes", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    rng = random.Random(SEED)

    raw = load_projects(args.readmes)
    personas = build_personas(rng)
    pm_of_portfolio = {PORTFOLIOS[k][0]: personas["pms"][k] for k in range(len(PORTFOLIOS))}

    projs = []
    for dirname, excerpt in raw:
        pid = assign_portfolio(dirname, excerpt)
        start, end = project_window(rng)
        projs.append({
            "dir": dirname,
            "title": title_from(dirname, excerpt),
            "portfolio": pid,
            "pm": pm_of_portfolio[pid]["name"],
            "em": rng.choice(personas["ems"])["name"],
            "window": {"start": start.isoformat(), "end": end.isoformat()},
            "n_emails": 4 if len(excerpt) > 1200 else 3,
            "readme_excerpt": excerpt,
        })

    contributors_of = {
        p["dir"]: [e["name"] for e in rng.sample(personas["engineers"], rng.randint(3, 4))]
        for p in projs
    }
    conflicts = build_conflicts(rng, projs, contributors_of)
    for p in projs:
        p["contributors"] = contributors_of[p["dir"]]
        p["conflicts"] = [
            {k: v for k, v in c.items() if k != "per_project"} | {"your_side": c["per_project"][p["dir"]]}
            for c in conflicts if p["dir"] in c["projects"]
        ]

    out = args.out
    (out / "company").mkdir(parents=True, exist_ok=True)
    (out / "batches").mkdir(parents=True, exist_ok=True)

    (out / "company" / "company.json").write_text(json.dumps({
        "name": "Meridian Research",
        "domain": DOMAIN,
        "fiction": "A fictional AI research company used to frame real open-source research projects as an internal product portfolio. All people, emails, dates, budgets and conflicts are synthetic.",
        "source": {"org": SOURCE_ORG, "repo": SOURCE_REPO, "license": "Apache-2.0",
                   "url": f"https://github.com/{SOURCE_ORG}/{SOURCE_REPO}"},
        "simulation_window": {"start": "2026-02-02", "end": "2026-08-15"},
    }, indent=2))
    (out / "company" / "personas.json").write_text(json.dumps(personas, indent=2))
    (out / "company" / "resources.json").write_text(json.dumps(resources(), indent=2))
    (out / "company" / "portfolios.json").write_text(json.dumps({
        "portfolios": [{"id": pid, "name": name, "pm": pm_of_portfolio[pid]["name"]} for pid, name, _ in PORTFOLIOS],
        "projects": [{k: p[k] for k in ("dir", "title", "portfolio", "pm", "em", "contributors", "window", "n_emails")} for p in projs],
    }, indent=2))
    (out / "company" / "conflict_map.json").write_text(json.dumps({"conflicts": conflicts}, indent=2))

    batches = [projs[k:k + BATCH_SIZE] for k in range(0, len(projs), BATCH_SIZE)]
    for bi, batch in enumerate(batches, 1):
        (out / "batches" / f"batch-{bi:02d}.json").write_text(json.dumps({
            "batch": bi,
            "company_files": ["company/company.json", "company/personas.json", "company/resources.json"],
            "projects": batch,
        }, indent=2))

    print(f"projects={len(projs)} conflicts={len(conflicts)} batches={len(batches)}")
    n_in_conflict = len({d for c in conflicts for d in c['projects']})
    print(f"projects_in_conflicts={n_in_conflict}")


if __name__ == "__main__":
    main()
