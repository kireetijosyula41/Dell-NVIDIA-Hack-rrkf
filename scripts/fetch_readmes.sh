#!/bin/sh
# Fetch the first 4KB of every top-level project README in a GitHub monorepo.
# Usage: fetch_readmes.sh <org> <repo> <branch> <outdir>
set -eu
ORG="${1:-google-research}"; REPO="${2:-google-research}"; BRANCH="${3:-master}"; OUT="${4:-readmes}"
mkdir -p "$OUT"
gh api "repos/$ORG/$REPO/git/trees/$BRANCH" --jq '.tree[] | select(.type=="tree") | .path' |
  grep -v '^\.' |
  while read -r d; do
    for f in README.md readme.md README.rst; do
      code=$(curl -s -o "$OUT/$d.md" -w "%{http_code}" -r 0-4095 \
        "https://raw.githubusercontent.com/$ORG/$REPO/$BRANCH/$d/$f")
      [ "$code" = "200" ] || [ "$code" = "206" ] && break
      rm -f "$OUT/$d.md"
    done
  done
echo "fetched: $(ls "$OUT" | wc -l | tr -d ' ') readmes -> $OUT"
