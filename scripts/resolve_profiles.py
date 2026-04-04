#!/usr/bin/env python3
"""Resolve one agent manifest's profile stack into a deterministic snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.profile_model import ProfileError, load_profiles, load_toml, resolve_profile_stack, validate_string_list


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_agent_manifest(path: Path) -> dict:
    config = load_toml(path)
    runtime = config.get("runtime")
    if not isinstance(runtime, dict):
        raise ProfileError(f"{path}: [runtime] is required")
    profiles = runtime.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ProfileError(f"{path}: runtime.profiles must be a non-empty array")
    if "skills" in runtime:
        validate_string_list(runtime["skills"], field_name=f"{path}: runtime.skills")
    return config


def resolve_agent_profiles(repo_root: Path, manifest_path: Path) -> dict:
    profiles = load_profiles(repo_root)
    manifest = load_agent_manifest(manifest_path)
    runtime = manifest["runtime"]
    resolved = resolve_profile_stack(runtime["profiles"], profiles)
    return {
        "agent_id": manifest["agent_id"],
        "name": manifest["name"],
        "role": manifest["role"],
        "requested_profiles": runtime["profiles"],
        "requested_skills": runtime.get("skills", []),
        "resolved_profile_stack": resolved["profile_stack"],
        "persona": resolved["persona"],
        "frontdoor": resolved["frontdoor"],
        "policy": resolved["policy"],
        "handoff": resolved["handoff"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="resolve_profiles")
    parser.add_argument("agent_manifest", help="Path to an agent.toml manifest")
    args = parser.parse_args(argv)
    try:
        snapshot = resolve_agent_profiles(REPO_ROOT, Path(args.agent_manifest).resolve())
    except (FileNotFoundError, ProfileError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
