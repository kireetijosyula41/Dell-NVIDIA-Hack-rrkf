#!/usr/bin/env python3
"""Summarize repositories in the google-research GitHub organization."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


ORG = "google-research"
API_ROOT = "https://api.github.com"
RAW_ROOT = "https://raw.githubusercontent.com"
TEXT_EXTENSIONS = (
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".py",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".ini",
    ".cfg",
    ".sh",
)
INTERESTING_ROOT_FILES = (
    "README.md",
    "README.rst",
    "README",
    "LICENSE",
    "LICENSE.txt",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements.in",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "environment.yml",
    "environment.yaml",
    "Dockerfile",
    "Makefile",
)
INTERESTING_DIR_PREFIXES = (
    "docs",
    "doc",
    "examples",
    "configs",
    "checkpoints",
    "models",
    "scripts",
    "notebooks",
    ".github",
)
RESOURCE_PATTERNS = {
    "papers": re.compile(r"(arxiv\.org|doi\.org|openreview\.net|research\.google)", re.I),
    "datasets": re.compile(r"(kaggle\.com|huggingface\.co/datasets|tfds|dataset)", re.I),
    "demos": re.compile(r"(colab\.research\.google\.com|demo|huggingface\.co/spaces)", re.I),
    "docs": re.compile(r"(readthedocs|docs\.|/docs/|documentation)", re.I),
    "checkpoints": re.compile(r"(checkpoint|weights|model\.ckpt|safetensors|\.pt\b|\.pth\b)", re.I),
}
CONSTRAINT_HINTS = (
    "requires",
    "requirement",
    "limitation",
    "limitations",
    "constraint",
    "constraints",
    "caveat",
    "caveats",
    "gpu",
    "tpu",
    "cuda",
    "only tested",
    "not supported",
    "apache beam",
)
SPEC_SECTION_HINTS = (
    "install",
    "installation",
    "setup",
    "requirements",
    "usage",
    "quickstart",
    "getting started",
)


@dataclass
class RepoFile:
    path: str
    kind: str
    download_url: str | None = None


def build_request(url: str) -> urllib.request.Request:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "openclaw-google-research-agent",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def fetch_json(url: str) -> Any:
    try:
        with urllib.request.urlopen(build_request(url)) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed for {url}: {exc.code} {body}") from exc


def fetch_text(url: str) -> str:
    try:
        with urllib.request.urlopen(build_request(url)) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return ""
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Text fetch failed for {url}: {exc.code} {body}") from exc


def fetch_repositories(limit: int) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1
    while len(repos) < limit:
        url = f"{API_ROOT}/orgs/{ORG}/repos?per_page=100&page={page}&sort=updated"
        batch = fetch_json(url)
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos[:limit]


def fetch_repo_metadata(full_name: str) -> dict[str, Any]:
    return fetch_json(f"{API_ROOT}/repos/{full_name}")


def fetch_contents(full_name: str, path: str = "") -> list[dict[str, Any]]:
    encoded_path = urllib.parse.quote(path)
    url = f"{API_ROOT}/repos/{full_name}/contents/{encoded_path}" if path else f"{API_ROOT}/repos/{full_name}/contents"
    payload = fetch_json(url)
    if isinstance(payload, dict):
        return [payload]
    return payload


def collect_repo_files(full_name: str) -> list[RepoFile]:
    entries = fetch_contents(full_name)
    repo_files: list[RepoFile] = []
    for entry in entries:
        name = entry["name"]
        path = entry["path"]
        if entry["type"] == "file" and is_interesting_root_file(name):
            repo_files.append(RepoFile(path=path, kind="file", download_url=entry.get("download_url")))
            continue
        if entry["type"] == "dir" and is_interesting_dir(name):
            repo_files.extend(collect_limited_directory(full_name, path))
    return repo_files


def collect_limited_directory(full_name: str, path: str, max_files: int = 12) -> list[RepoFile]:
    files: list[RepoFile] = []
    for entry in fetch_contents(full_name, path):
        if len(files) >= max_files:
            break
        if entry["type"] == "file" and looks_like_text(entry["name"]):
            files.append(RepoFile(path=entry["path"], kind="file", download_url=entry.get("download_url")))
        elif entry["type"] == "dir" and path.count("/") < 1:
            files.extend(collect_limited_directory(full_name, entry["path"], max_files=max_files - len(files)))
    return files[:max_files]


def is_interesting_root_file(name: str) -> bool:
    return name in INTERESTING_ROOT_FILES or (name.startswith("README") and looks_like_text(name))


def is_interesting_dir(name: str) -> bool:
    lowered = name.lower()
    return any(lowered.startswith(prefix) for prefix in INTERESTING_DIR_PREFIXES)


def looks_like_text(name: str) -> bool:
    lowered = name.lower()
    return lowered.endswith(TEXT_EXTENSIONS) or lowered in {"dockerfile", "makefile", "license", "readme"}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_overview(readme: str, fallback: str | None) -> str:
    paragraphs = [normalize_whitespace(block) for block in re.split(r"\n\s*\n", readme) if block.strip()]
    for paragraph in paragraphs:
        if paragraph.startswith("#"):
            continue
        if len(paragraph) >= 40:
            return paragraph
    return fallback or ""


def extract_urls(text: str) -> list[str]:
    return sorted(set(re.findall(r"https?://[^\s)>\]]+", text)))


def extract_sections(readme: str, hints: tuple[str, ...]) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_heading = "intro"
    buffer: list[str] = []
    for line in readme.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if heading_match:
            if buffer:
                content = "\n".join(buffer).strip()
                if heading_matches(current_heading, hints) and content:
                    sections.append({"heading": current_heading, "content": content})
            current_heading = heading_match.group(2).strip()
            buffer = []
            continue
        buffer.append(line)
    if buffer:
        content = "\n".join(buffer).strip()
        if heading_matches(current_heading, hints) and content:
            sections.append({"heading": current_heading, "content": content})
    return sections


def heading_matches(heading: str, hints: tuple[str, ...]) -> bool:
    lowered = heading.lower()
    return any(hint in lowered for hint in hints)


def select_constraint_lines(text: str, limit: int = 8) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip(" -*\t")
        lowered = line.lower()
        if len(line) < 30 or line.startswith("("):
            continue
        if any(hint in lowered for hint in CONSTRAINT_HINTS):
            lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def parse_dependency_files(files: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "dependency_files": sorted(files.keys()),
        "python_dependencies": [],
        "framework_signals": [],
    }
    deps: set[str] = set()
    frameworks: set[str] = set()
    for path, text in files.items():
        lowered = text.lower()
        if path.endswith((".txt", ".in")):
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                deps.add(re.split(r"[<>=\[]", line, maxsplit=1)[0].strip())
        if path.endswith((".toml", ".cfg", ".py", ".yml", ".yaml")):
            for token in ("tensorflow", "jax", "flax", "pytorch", "torch", "transformers", "numpy", "scikit-learn"):
                if token in lowered:
                    frameworks.add(token)
    result["python_dependencies"] = sorted(dep for dep in deps if dep)[:30]
    result["framework_signals"] = sorted(frameworks)
    return result


def classify_resources(urls: list[str]) -> dict[str, list[str]]:
    resources: dict[str, list[str]] = {key: [] for key in RESOURCE_PATTERNS}
    for url in urls:
        for key, pattern in RESOURCE_PATTERNS.items():
            if pattern.search(url):
                resources[key].append(url)
    return {key: sorted(set(values)) for key, values in resources.items() if values}


def infer_runtime_constraints(meta: dict[str, Any], files: dict[str, str]) -> list[str]:
    constraints: list[str] = []
    if meta.get("archived"):
        constraints.append("Repository is archived.")
    if not meta.get("has_issues", False):
        constraints.append("Issues are disabled, which limits public maintenance signals.")
    combined = "\n".join(files.values()).lower()
    if "cuda" in combined or "gpu" in combined or "tpu" in combined:
        constraints.append("Repository likely expects accelerator hardware for full use or reproduction.")
    if any(os.path.basename(path).lower() == "dockerfile" for path in files):
        constraints.append("Docker support is present; environment may be expected to match container assumptions.")
    return constraints


def summarize_repo(full_name: str) -> dict[str, Any]:
    meta = fetch_repo_metadata(full_name)
    repo_files = collect_repo_files(full_name)
    file_text: dict[str, str] = {}
    evidence_files: list[str] = []
    all_urls: list[str] = []

    for repo_file in repo_files:
        if not repo_file.download_url:
            default_branch = meta["default_branch"]
            repo_file.download_url = f"{RAW_ROOT}/{full_name}/{default_branch}/{repo_file.path}"
        text = fetch_text(repo_file.download_url)
        if not text:
            continue
        file_text[repo_file.path] = text[:50000]
        evidence_files.append(repo_file.path)
        all_urls.extend(extract_urls(text))

    readme_text = ""
    for candidate in ("README.md", "README.rst", "README"):
        if candidate in file_text:
            readme_text = file_text[candidate]
            break

    dependency_files = {
        path: text
        for path, text in file_text.items()
        if path.endswith((".txt", ".in", ".toml", ".cfg", ".py", ".yml", ".yaml"))
        or path in {"Dockerfile", "Makefile"}
    }
    dependency_summary = parse_dependency_files(dependency_files)
    spec_sections = extract_sections(readme_text, SPEC_SECTION_HINTS)[:6]
    explicit_constraints = extract_sections(readme_text, ("limitations", "limitation", "caveats", "notes", "warning"))
    constraint_lines = select_constraint_lines(readme_text)
    resources = classify_resources(all_urls)
    inferred_constraints = infer_runtime_constraints(meta, file_text)

    project_overview = extract_overview(readme_text, meta.get("description")) if readme_text else (meta.get("description") or "")

    return {
        "repository": full_name,
        "project_information": {
            "name": meta["name"],
            "full_name": meta["full_name"],
            "description": meta.get("description"),
            "overview": project_overview or meta.get("description"),
            "homepage": meta.get("homepage"),
            "topics": meta.get("topics", []),
            "license": (meta.get("license") or {}).get("spdx_id"),
            "default_branch": meta.get("default_branch"),
            "archived": meta.get("archived"),
            "language": meta.get("language"),
            "stargazers_count": meta.get("stargazers_count"),
            "forks_count": meta.get("forks_count"),
            "open_issues_count": meta.get("open_issues_count"),
            "created_at": meta.get("created_at"),
            "updated_at": meta.get("updated_at"),
            "pushed_at": meta.get("pushed_at"),
        },
        "specs": {
            "dependency_summary": dependency_summary,
            "readme_sections": spec_sections,
        },
        "constraints": {
            "explicit_sections": explicit_constraints[:4],
            "explicit_lines": constraint_lines,
            "inferred": inferred_constraints,
        },
        "resources": resources,
        "evidence": {
            "files_inspected": evidence_files,
            "urls_found": sorted(set(all_urls))[:100],
        },
    }


def format_markdown(reports: list[dict[str, Any]]) -> str:
    lines: list[str] = ["# Google Research Repository Digest", ""]
    for report in reports:
        info = report["project_information"]
        specs = report["specs"]
        constraints = report["constraints"]
        resources = report["resources"]
        evidence = report["evidence"]
        lines.extend(
            [
                f"## {info['full_name']}",
                "",
                "### Project Information",
                f"- Description: {info.get('description') or 'n/a'}",
                f"- Overview: {info.get('overview') or 'n/a'}",
                f"- License: {info.get('license') or 'n/a'}",
                f"- Language: {info.get('language') or 'n/a'}",
                f"- Topics: {', '.join(info.get('topics') or []) or 'n/a'}",
                f"- Default branch: {info.get('default_branch') or 'n/a'}",
                f"- Archived: {info.get('archived')}",
                f"- Stars: {info.get('stargazers_count')}",
                f"- Last push: {info.get('pushed_at') or 'n/a'}",
                "",
                "### Specs",
                f"- Dependency files: {', '.join(specs['dependency_summary']['dependency_files']) or 'n/a'}",
                f"- Python dependencies: {', '.join(specs['dependency_summary']['python_dependencies']) or 'n/a'}",
                f"- Framework signals: {', '.join(specs['dependency_summary']['framework_signals']) or 'n/a'}",
            ]
        )
        if specs["readme_sections"]:
            lines.append("- Notable README sections:")
            for section in specs["readme_sections"]:
                snippet = normalize_whitespace(section["content"])[:240]
                lines.append(f"  - {section['heading']}: {snippet}")
        else:
            lines.append("- Notable README sections: n/a")
        lines.extend(["", "### Constraints"])
        combined_constraints = constraints["explicit_lines"] + constraints["inferred"]
        if combined_constraints:
            for item in combined_constraints[:10]:
                lines.append(f"- {item}")
        else:
            lines.append("- No clear constraints detected from inspected files.")
        if constraints["explicit_sections"]:
            lines.append("- Constraint-related sections:")
            for section in constraints["explicit_sections"]:
                snippet = normalize_whitespace(section["content"])[:240]
                lines.append(f"  - {section['heading']}: {snippet}")
        lines.extend(["", "### Resources"])
        if resources:
            for key, urls in sorted(resources.items()):
                lines.append(f"- {key.title()}: {', '.join(urls[:5])}")
        else:
            lines.append("- No categorized external resources found.")
        lines.extend(
            [
                "",
                "### Evidence",
                f"- Files inspected: {', '.join(evidence['files_inspected']) or 'n/a'}",
                f"- URLs found: {len(evidence['urls_found'])}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect structured summaries for repositories in google-research."
    )
    parser.add_argument("--limit", type=int, default=10, help="Maximum repositories to inspect when --repo is not provided.")
    parser.add_argument("--repo", action="append", default=[], help="Specific repository full name, for example google-research/timesfm.")
    parser.add_argument(
        "--output",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument("--output-file", help="Optional file path for the generated report.")
    return parser.parse_args(argv)


def write_output(content: str, output_file: str | None) -> None:
    if output_file:
        with open(output_file, "w", encoding="utf-8") as handle:
            handle.write(content)
        return
    sys.stdout.write(content)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repos = args.repo or [item["full_name"] for item in fetch_repositories(args.limit)]
    reports = [summarize_repo(full_name) for full_name in repos]
    if args.output == "json":
        content = json.dumps(reports, indent=2)
    else:
        content = format_markdown(reports)
    write_output(content + ("" if content.endswith("\n") else "\n"), args.output_file)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        raise SystemExit(130)
    except RuntimeError as exc:
        message = textwrap.fill(str(exc), width=100)
        print(message, file=sys.stderr)
        raise SystemExit(1)
