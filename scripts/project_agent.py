#!/usr/bin/env python3
"""Project a resolved agent profile stack into context-repo seed artifacts."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
import tomllib

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.profile_model import ProfileError, load_toml
from scripts.resolve_profiles import resolve_agent_profiles


DEFAULT_LAYOUT = {
    "bundles_dir": "bundles",
    "memory_dir": "memory",
    "artifacts_dir": "artifacts",
    "runs_dir": "runs",
}


class ProjectionError(Exception):
    """Raised when projecting an agent profile into a context repo fails."""


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ProjectionError(message)


def discover_workspace_root(agent_manifest: Path) -> Path:
    current = agent_manifest.resolve().parent
    while current != current.parent:
        if (current / "agents.toml").exists():
            return current
        current = current.parent
    raise ProjectionError(f"could not locate workspace root for {agent_manifest}")


def load_context_repo_config(context_repo: Path) -> dict[str, object]:
    config_path = context_repo / "skillfoundry.toml"
    ensure(config_path.exists(), f"{context_repo}: missing skillfoundry.toml")
    try:
        return tomllib.loads(config_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ProjectionError(f"{config_path}: invalid TOML: {exc}") from exc


def resolve_layout(context_repo: Path) -> dict[str, Path]:
    config = load_context_repo_config(context_repo)
    layout = config.get("layout", {})
    ensure(isinstance(layout, dict), f"{context_repo / 'skillfoundry.toml'}: [layout] must be a table when present")
    return {
        key: context_repo / str(layout.get(key, default))
        for key, default in DEFAULT_LAYOUT.items()
    }


def validate_frontdoor_pin(context_repo: Path, memory_dir: Path, relative_memory_path: str) -> None:
    config = load_context_repo_config(context_repo)
    frontdoor = config.get("frontdoor")
    ensure(isinstance(frontdoor, dict), f"{context_repo / 'skillfoundry.toml'}: [frontdoor] is required")
    pinned_paths = frontdoor.get("pinned_paths")
    ensure(isinstance(pinned_paths, list), f"{context_repo / 'skillfoundry.toml'}: frontdoor.pinned_paths must be an array")
    expected = (memory_dir.relative_to(context_repo) / relative_memory_path).as_posix()
    ensure(expected in pinned_paths, f"{context_repo}: frontdoor must pin {expected!r} before projection")


def render_profile_markdown(snapshot: dict[str, object]) -> str:
    persona = snapshot["persona"]
    frontdoor = snapshot["frontdoor"]
    policy = snapshot["policy"]
    handoff = snapshot["handoff"]
    lines = [
        f"# Agent Profile: {snapshot['name']}",
        "",
        f"- agent_id: {snapshot['agent_id']}",
        f"- role: {snapshot['role']}",
        f"- requested_profiles: {', '.join(snapshot['requested_profiles'])}",
        f"- requested_skills: {', '.join(snapshot['requested_skills']) if snapshot['requested_skills'] else '(none declared)'}",
        f"- resolved_profile_stack: {', '.join(snapshot['resolved_profile_stack'])}",
        "",
        "## Persona",
        "",
        str(persona.get("summary", "")),
        "",
        "## Mission",
        "",
    ]
    for entry in frontdoor["mission"]:
        lines.append(f"- {entry}")
    lines.extend(["", "## Focus", ""])
    for entry in frontdoor["focus"]:
        lines.append(f"- {entry}")
    lines.extend(["", "## Deliverables", ""])
    for entry in frontdoor["deliverables"]:
        lines.append(f"- {entry}")
    lines.extend(["", "## Promotion Policy Hints", ""])
    for entry in policy["promotion_validation_kinds"]:
        lines.append(f"- validation: {entry}")
    for entry in policy["preferred_bundle_ids"]:
        lines.append(f"- preferred_bundle: {entry}")
    lines.extend(["", "## Handoff", ""])
    for entry in handoff["expected_outputs"]:
        lines.append(f"- expected_output: {entry}")
    for entry in handoff["downstream_profiles"]:
        lines.append(f"- downstream_profile: {entry}")
    lines.append("")
    return "\n".join(lines)


def build_profile_bundle(snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "bundle_id": f"{snapshot['agent_id']}-profile",
        "purpose": f"Resolved role profile stack for agent {snapshot['agent_id']} used to seed front-door behavior.",
        "owners": [
            {
                "name": "skillfoundry-agents",
                "contact": "workspace://skillfoundry-agents",
            }
        ],
        "sources": [
            {
                "kind": "doc",
                "locator": f"skillfoundry-agents://agents/{snapshot['agent_id']}/profiles",
                "captured_at": utc_now(),
                "notes": f"Requested profiles: {', '.join(snapshot['requested_profiles'])}",
            }
        ],
        "content": [
            {
                "id": "persona",
                "type": "summary",
                "body": snapshot["persona"]["summary"],
                "source_refs": [0],
            },
            {
                "id": "mission",
                "type": "instruction",
                "body": "\n".join(snapshot["frontdoor"]["mission"]),
                "source_refs": [0],
            },
            {
                "id": "focus",
                "type": "constraint",
                "body": "\n".join(snapshot["frontdoor"]["focus"]),
                "source_refs": [0],
            },
            {
                "id": "deliverables",
                "type": "example",
                "body": "\n".join(snapshot["frontdoor"]["deliverables"]),
                "source_refs": [0],
            },
        ],
        "promotion": {
            "status": "promoted",
            "reviewed_at": utc_now(),
            "compatibility": "additive",
            "notes": f"Resolved profile stack: {', '.join(snapshot['resolved_profile_stack'])}",
        },
    }


def write_projection(agent_manifest: Path, context_repo: Path) -> dict[str, str]:
    manifest_path = agent_manifest.resolve()
    workspace_root = discover_workspace_root(manifest_path)
    snapshot = resolve_agent_profiles(workspace_root, manifest_path)
    manifest = load_toml(manifest_path)
    projection = manifest["projection"]
    layout = resolve_layout(context_repo)
    memory_target = layout["memory_dir"] / projection["memory_profile_path"]
    bundle_target = layout["bundles_dir"] / projection["bundle_profile_path"]
    if projection.get("require_frontdoor_pin", False):
        validate_frontdoor_pin(context_repo, layout["memory_dir"], projection["memory_profile_path"])
    memory_target.parent.mkdir(parents=True, exist_ok=True)
    bundle_target.parent.mkdir(parents=True, exist_ok=True)
    memory_target.write_text(render_profile_markdown(snapshot))
    bundle_target.write_text(json.dumps(build_profile_bundle(snapshot), indent=2, sort_keys=True) + "\n")
    return {
        "memory_profile_path": str(memory_target.relative_to(context_repo)),
        "bundle_profile_path": str(bundle_target.relative_to(context_repo)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="project_agent")
    parser.add_argument("agent_manifest", help="Path to the agent.toml manifest")
    parser.add_argument("context_repo", help="Path to the target context repository")
    args = parser.parse_args(argv)
    try:
        result = write_projection(Path(args.agent_manifest), Path(args.context_repo).resolve())
    except (FileNotFoundError, ProfileError, ProjectionError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
