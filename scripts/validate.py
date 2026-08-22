#!/usr/bin/env python3
"""Validate the generated corpus against the plan and write the manifest.

Checks per project: files present, email count matches plan, JSON parses, senders/
recipients exist in personas.json, dates inside window and increasing per thread,
every planned conflict logged in ground_truth.json with claims planted in real emails.

Usage: validate.py [--root .] [--dataset google-research] [--write-manifest]
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--dataset", default="google-research")
    ap.add_argument("--write-manifest", action="store_true")
    args = ap.parse_args()
    root = args.root

    personas = json.loads((root / "company/personas.json").read_text())
    known = {p["email"] for group in personas.values() for p in group}
    plan = {p["dir"]: p for p in json.loads((root / "company/portfolios.json").read_text())["projects"]}
    conflict_map = json.loads((root / "company/conflict_map.json").read_text())["conflicts"]
    planned_conflicts = {c["id"]: c for c in conflict_map}

    proj_root = root / "datasets" / args.dataset / "projects"
    errors, manifest_rows, n_emails_total = [], [], 0
    seen_conflict_plants = set()

    for dirname, planned in sorted(plan.items()):
        pdir = proj_root / dirname
        err = lambda m: errors.append(f"{dirname}: {m}")
        if not pdir.is_dir():
            err("missing project directory")
            continue
        try:
            pj = json.loads((pdir / "project.json").read_text())
            gt = json.loads((pdir / "ground_truth.json").read_text())
            email_files = sorted((pdir / "emails").glob("e*.json"))
            emails = {f.stem: json.loads(f.read_text()) for f in email_files}
        except Exception as e:
            err(f"unreadable JSON: {e}")
            continue
        if len(emails) != planned["n_emails"]:
            err(f"expected {planned['n_emails']} emails, found {len(emails)}")
        w0 = datetime.fromisoformat(planned["window"]["start"] + "T00:00:00+00:00")
        w1 = datetime.fromisoformat(planned["window"]["end"] + "T23:59:59+00:00")
        last_by_thread = {}
        for eid, em in sorted(emails.items()):
            for fld in ("from",):
                if em[fld]["email"] not in known:
                    err(f"{eid}: unknown sender {em[fld]['email']}")
            for fld in ("to", "cc"):
                for r in em.get(fld) or []:
                    if r["email"] not in known:
                        err(f"{eid}: unknown recipient {r['email']}")
            try:
                d = datetime.fromisoformat(em["date"].replace("Z", "+00:00"))
                if not (w0 <= d <= w1):
                    err(f"{eid}: date {em['date']} outside window")
                t = em.get("thread_id")
                if t in last_by_thread and d <= last_by_thread[t]:
                    err(f"{eid}: dates not increasing in thread {t}")
                last_by_thread[t] = d
            except Exception as e:
                err(f"{eid}: bad date: {e}")
        planned_ids = {c["id"] for c in planned.get("conflicts", [])} if "conflicts" in planned else {
            c["id"] for c in conflict_map if dirname in c["projects"]}
        logged = {c["conflict_id"] for c in gt.get("conflicts", [])}
        for missing in planned_ids - logged:
            err(f"conflict {missing} planned but not logged in ground_truth.json")
        for c in gt.get("conflicts", []):
            if c["conflict_id"] not in planned_conflicts:
                err(f"ground truth logs unknown conflict {c['conflict_id']}")
            for ref in c.get("planted_in", []):
                if ref not in emails:
                    err(f"conflict {c['conflict_id']} planted_in {ref} which does not exist")
            seen_conflict_plants.add((c["conflict_id"], dirname))
        n_emails_total += len(emails)
        manifest_rows.append({
            "id": f"gr/{dirname}", "dir": dirname, "title": planned["title"],
            "portfolio": planned["portfolio"], "pm": planned["pm"],
            "n_emails": len(emails), "conflict_ids": sorted(planned_ids),
        })

    for c in conflict_map:
        for d in c["projects"]:
            if d in plan and (proj_root / d).is_dir() and (c["id"], d) not in seen_conflict_plants:
                errors.append(f"{d}: conflict {c['id']} has no plant record")

    print(f"projects checked: {len(manifest_rows)}/{len(plan)}  emails: {n_emails_total}  errors: {len(errors)}")
    for e in errors[:60]:
        print("  ERROR", e)
    if len(errors) > 60:
        print(f"  ... and {len(errors) - 60} more")

    if args.write_manifest:
        (root / "datasets" / args.dataset / "manifest.json").write_text(json.dumps({
            "dataset": args.dataset,
            "company": "Meridian Research",
            "projects": len(manifest_rows),
            "emails": n_emails_total,
            "conflicts": len(conflict_map),
            "index": manifest_rows,
        }, indent=2))
        print("manifest written")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
