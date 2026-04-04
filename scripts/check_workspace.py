#!/usr/bin/env python3
"""Validate the hub workspace layout for Skillfoundry agents."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.profile_model import ProfileError, load_profiles, validate_string_list


REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_ROOT_ENTRIES = {"contract", "examples", "bundles", "memory", "artifacts", "runs"}
FORBIDDEN_AGENT_DIR_ENTRIES = {"bundles", "memory", "artifacts", "runs"}
ALLOWED_AGENT_STATUSES = {"planned", "active", "paused", "retired"}


class WorkspaceError(Exception):
    """Raised when the hub workspace layout is invalid."""


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise WorkspaceError(message)


def load_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise WorkspaceError(f"{path}: invalid TOML: {exc}") from exc


def raise_profile_as_workspace_error(fn):
    try:
        return fn()
    except ProfileError as exc:
        raise WorkspaceError(str(exc)) from exc


def validate_workspace_config(repo_root: Path) -> tuple[str, dict[str, str]]:
    workspace_config = repo_root / "agents.toml"
    ensure(workspace_config.exists(), f"missing workspace config: {workspace_config}")
    config = load_toml(workspace_config)
    ensure(config.get("schema_version") == "1", f"{workspace_config}: schema_version must be '1'")
    workspace_name = config.get("workspace_name")
    ensure(isinstance(workspace_name, str) and workspace_name.strip(), f"{workspace_config}: workspace_name required")
    harness = config.get("harness")
    ensure(isinstance(harness, dict), f"{workspace_config}: [harness] is required")
    ensure(harness.get("package") == "skillfoundry-harness", f"{workspace_config}: harness.package must be 'skillfoundry-harness'")
    ensure(
        harness.get("context_repo_config") == "skillfoundry.toml",
        f"{workspace_config}: harness.context_repo_config must be 'skillfoundry.toml'",
    )
    ensure(
        harness.get("context_repo_schema_version") == "1",
        f"{workspace_config}: harness.context_repo_schema_version must be '1'",
    )
    defaults = config.get("defaults", {})
    ensure(isinstance(defaults, dict), f"{workspace_config}: [defaults] must be a table")
    context_dir_name = defaults.get("context_dir_name", "context")
    ensure(context_dir_name == "context", f"{workspace_config}: only context_dir_name='context' is currently supported")
    agent_entries = config.get("agents", [])
    ensure(isinstance(agent_entries, list) and agent_entries, f"{workspace_config}: at least one [[agents]] entry is required")

    registry: dict[str, str] = {}
    for index, entry in enumerate(agent_entries):
        ensure(isinstance(entry, dict), f"{workspace_config}: agents[{index}] must be a table")
        for key in ("agent_id", "path"):
            ensure(key in entry, f"{workspace_config}: agents[{index}].{key} is required")
        ensure(set(entry).issubset({"agent_id", "path"}), f"{workspace_config}: agents[{index}] has unexpected keys")
        agent_id = entry["agent_id"]
        ensure(isinstance(agent_id, str) and agent_id.strip(), f"{workspace_config}: agents[{index}].agent_id invalid")
        ensure(agent_id not in registry, f"{workspace_config}: duplicate agent_id {agent_id!r}")
        path = entry["path"]
        ensure(isinstance(path, str) and path.strip(), f"{workspace_config}: agents[{index}].path invalid")
        registry[agent_id] = path
    return context_dir_name, registry


def validate_projection(config: dict, manifest: Path) -> None:
    ensure(isinstance(config, dict), f"{manifest}: [projection] must be a table")
    ensure(set(config).issubset({"memory_profile_path", "bundle_profile_path", "require_frontdoor_pin"}), f"{manifest}: unexpected keys in [projection]")
    for key in ("memory_profile_path", "bundle_profile_path"):
        ensure(key in config, f"{manifest}: projection.{key} is required")
        value = config[key]
        ensure(isinstance(value, str) and value.strip(), f"{manifest}: projection.{key} must be a non-empty string")
        ensure(not value.startswith("/"), f"{manifest}: projection.{key} must be relative")
        ensure(".." not in Path(value).parts, f"{manifest}: projection.{key} must stay inside the target scope")
    if "require_frontdoor_pin" in config:
        ensure(isinstance(config["require_frontdoor_pin"], bool), f"{manifest}: projection.require_frontdoor_pin must be boolean")


def validate_git_backed_checkout(path: Path) -> None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise WorkspaceError(f"{path}: expected git-backed context checkout") from exc
    ensure(result.stdout.strip() == "true", f"{path}: expected git-backed context checkout")


def validate_agent(agent_dir: Path, context_dir_name: str, profile_registry: dict[str, dict]) -> None:
    manifest = agent_dir / "agent.toml"
    ensure(manifest.exists(), f"{agent_dir}: missing agent.toml")
    config = load_toml(manifest)
    ensure(config.get("schema_version") == "1", f"{manifest}: schema_version must be '1'")
    ensure(config.get("agent_id") == agent_dir.name, f"{manifest}: agent_id must match directory name")
    for key in ("name", "role", "context_mount_path", "status", "purpose", "runtime", "projection"):
        ensure(key in config, f"{manifest}: {key} is required")
    ensure(isinstance(config["purpose"], dict), f"{manifest}: [purpose] must be a table")
    ensure(
        isinstance(config["purpose"].get("summary"), str) and config["purpose"]["summary"].strip(),
        f"{manifest}: purpose.summary is required",
    )
    ensure(isinstance(config["runtime"], dict), f"{manifest}: [runtime] must be a table")
    ensure(set(config["runtime"]).issubset({"profiles", "skills"}), f"{manifest}: unexpected keys in [runtime]")
    ensure("profiles" in config["runtime"], f"{manifest}: runtime.profiles is required")
    profile_ids = validate_string_list(config["runtime"]["profiles"], field_name=f"{manifest}: runtime.profiles")
    ensure(profile_ids, f"{manifest}: runtime.profiles must contain at least one profile")
    for profile_id in profile_ids:
        ensure(profile_id in profile_registry, f"{manifest}: runtime.profiles references unknown profile {profile_id!r}")
    if "skills" in config["runtime"]:
        validate_string_list(config["runtime"]["skills"], field_name=f"{manifest}: runtime.skills")
    validate_projection(config["projection"], manifest)
    ensure(config["context_mount_path"] == context_dir_name, f"{manifest}: context_mount_path must be {context_dir_name!r}")
    ensure(config["status"] in ALLOWED_AGENT_STATUSES, f"{manifest}: status must be one of {sorted(ALLOWED_AGENT_STATUSES)}")

    for name in FORBIDDEN_AGENT_DIR_ENTRIES:
        ensure(not (agent_dir / name).exists(), f"{agent_dir / name}: agent state must live under {context_dir_name}/")

    context_path = agent_dir / context_dir_name
    if context_path.exists():
        ensure(context_path.is_dir(), f"{context_path}: expected directory")
        ensure((context_path / "skillfoundry.toml").exists(), f"{context_path}: missing skillfoundry.toml")
        validate_git_backed_checkout(context_path)
    if config["status"] in {"active", "paused"}:
        ensure(context_path.exists(), f"{manifest}: status {config['status']!r} requires a mounted {context_dir_name}/ checkout")


def validate_workspace(repo_root: Path = REPO_ROOT) -> None:
    agents_dir = repo_root / "agents"
    workspace_config = repo_root / "agents.toml"
    context_dir_name, registry = validate_workspace_config(repo_root)
    profile_registry = raise_profile_as_workspace_error(lambda: load_profiles(repo_root))
    ensure(agents_dir.exists(), f"missing agents directory: {agents_dir}")
    for name in sorted(FORBIDDEN_ROOT_ENTRIES):
        ensure(not (repo_root / name).exists(), f"{repo_root / name}: forbidden at hub root")
    discovered = {path.name: path for path in agents_dir.iterdir() if path.is_dir() and not path.name.startswith(".")}
    ensure(discovered, f"{agents_dir}: at least one agent directory is required")
    ensure(set(discovered) == set(registry), f"{agents_dir}: directory set must match agents.toml registry")

    for agent_id, agent_dir in sorted(discovered.items()):
        ensure(registry[agent_id] == str(agent_dir.relative_to(repo_root)), f"{workspace_config}: path for {agent_id} must match directory")
        validate_agent(agent_dir, context_dir_name, profile_registry)


def main() -> int:
    try:
        validate_workspace()
    except WorkspaceError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    print("OK workspace checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
