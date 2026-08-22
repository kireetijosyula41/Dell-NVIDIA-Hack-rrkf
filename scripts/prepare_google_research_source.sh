#!/usr/bin/env bash
# Create a shallow sparse checkout containing only CEO Brain's project paths.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_ROOT="${GOOGLE_RESEARCH_SOURCE_ROOT:-$ROOT_DIR/.cache/google-research-source}"

command -v git >/dev/null || { echo "git is required." >&2; exit 1; }

if [ ! -d "$SOURCE_ROOT/.git" ]; then
  git clone --depth 1 --filter=blob:none --sparse https://github.com/google-research/google-research.git "$SOURCE_ROOT"
fi

project_paths=$(python3 - <<PY
import json
from pathlib import Path
for project_file in sorted(Path("$ROOT_DIR/datasets/google-research/projects").glob("*/project.json")):
    print(json.loads(project_file.read_text(encoding="utf-8"))["source"]["path"])
PY
)

git -C "$SOURCE_ROOT" sparse-checkout set --no-cone $project_paths
git -C "$SOURCE_ROOT" checkout -f
printf '%s\n' "$SOURCE_ROOT"
