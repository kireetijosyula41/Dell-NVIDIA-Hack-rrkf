# Google Research OpenClaw Agent

This repository contains a pre-seeded OpenClaw workspace for a research analyst
agent that reviews public repositories under
[`google-research`](https://github.com/google-research) and produces structured
project summaries.

The agent is designed to gather:

- project information
- technical specs
- constraints and caveats
- linked resources such as papers, datasets, demos, and docs

## Workspace layout

- `openclaw-google-research-agent/`: OpenClaw workspace files
- `openclaw-google-research-agent/tools/google_research_digest.py`: helper script

## What the helper script does

The script talks to the public GitHub API and inspects common repository files
such as:

- `README*`
- `LICENSE*`
- `requirements*.txt`
- `pyproject.toml`
- `setup.py`
- `environment.yml`
- `Dockerfile`
- `docs/`
- `.github/`

It then writes either JSON or Markdown summaries that capture the repo's:

- metadata
- specs
- constraints
- resources
- evidence sources

## Usage

Run against a small slice of the org:

```bash
python3 openclaw-google-research-agent/tools/google_research_digest.py \
  --limit 5 \
  --output markdown \
  --output-file report.md
```

Target specific repositories:

```bash
python3 openclaw-google-research-agent/tools/google_research_digest.py \
  --repo google-research/timesfm \
  --repo google-research/federated \
  --output json \
  --output-file report.json
```

Use a GitHub token if you want a higher API rate limit:

```bash
export GITHUB_TOKEN=your_token_here
```

## Using with OpenClaw

Point an OpenClaw agent workspace at
`openclaw-google-research-agent/`. The required workspace files are already
included:

- `AGENTS.md`
- `SOUL.md`
- `IDENTITY.md`
- `USER.md`
- `BOOTSTRAP.md`

If you want to bind it as its own agent in OpenClaw, use the workspace path:

```bash
openclaw agents add google-research-analyst \
  --workspace /Users/kireetijosyula/Downloads/Dell-NVIDIA-Hack-rrkf/openclaw-google-research-agent
```
