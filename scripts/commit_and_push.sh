#!/bin/sh
# Commit each generated project directory as its own commit and push one by one.
# Skips projects that are not yet complete or already committed. Safe to re-run.
# Usage: commit_and_push.sh [--no-push] [dataset]
set -eu
cd "$(git rev-parse --show-toplevel)"
PUSH=1
[ "${1:-}" = "--no-push" ] && { PUSH=0; shift; }
DATASET="${1:-google-research}"
ROOT="datasets/$DATASET/projects"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

for pdir in "$ROOT"/*/; do
  d="$(basename "$pdir")"
  [ -f "$pdir/project.json" ] && [ -f "$pdir/ground_truth.json" ] || continue
  ls "$pdir/emails"/e*.json >/dev/null 2>&1 || continue
  # skip if already committed and unchanged
  if git ls-files --error-unmatch "$pdir" >/dev/null 2>&1 && \
     git diff --quiet HEAD -- "$pdir" 2>/dev/null && \
     [ -z "$(git status --porcelain -- "$pdir")" ]; then
    continue
  fi
  n="$(ls "$pdir/emails"/e*.json | wc -l | tr -d ' ')"
  git add -- "$pdir"
  git commit -q -m "dataset(gr/$d): add $n synthetic stakeholder emails + ground truth

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012bHuSfNUJCMZyeVhVEizXq" || continue
  echo "committed $d"
  if [ "$PUSH" = 1 ]; then
    ok=0
    for attempt in 1 2 3; do
      if git push -q origin "$BRANCH"; then ok=1; break; fi
      echo "push failed for $d (attempt $attempt), retrying in 5s" >&2
      sleep 5
    done
    [ "$ok" = 1 ] || { echo "giving up pushing at $d; commits remain local" >&2; exit 1; }
  fi
done
echo "done: $(git rev-list --count HEAD) commits total on $BRANCH"
