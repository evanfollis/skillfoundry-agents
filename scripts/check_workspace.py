#!/usr/bin/env python3
"""Validate the hub workspace layout for Skillfoundry agents."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


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


def validate_agent(agent_dir: Path, context_dir_name: str) -> None:
    manifest = agent_dir / "agent.toml"
    ensure(manifest.exists(), f"{agent_dir}: missing agent.toml")
    config = load_toml(manifest)
    ensure(config.get("schema_version") == "1", f"{manifest}: schema_version must be '1'")
    ensure(config.get("agent_id") == agent_dir.name, f"{manifest}: agent_id must match directory name")
    for key in ("name", "role", "context_submodule_path", "status"):
        ensure(key in config, f"{manifest}: {key} is required")
    ensure(config["context_submodule_path"] == context_dir_name, f"{manifest}: context_submodule_path must be {context_dir_name!r}")
    ensure(config["status"] in ALLOWED_AGENT_STATUSES, f"{manifest}: status must be one of {sorted(ALLOWED_AGENT_STATUSES)}")

    for name in FORBIDDEN_AGENT_DIR_ENTRIES:
        ensure(not (agent_dir / name).exists(), f"{agent_dir / name}: agent state must live under {context_dir_name}/")

    context_path = agent_dir / context_dir_name
    if context_path.exists():
        ensure(context_path.is_dir(), f"{context_path}: expected directory")
        ensure(
            (context_path / ".git").exists() or context_path.joinpath(".git").is_file(),
            f"{context_path}: expected git submodule checkout",
        )
    if config["status"] in {"active", "paused"}:
        ensure(context_path.exists(), f"{manifest}: status {config['status']!r} requires a checked-out {context_dir_name}/")


def validate_workspace(repo_root: Path = REPO_ROOT) -> None:
    agents_dir = repo_root / "agents"
    workspace_config = repo_root / "agents.toml"
    context_dir_name, registry = validate_workspace_config(repo_root)
    ensure(agents_dir.exists(), f"missing agents directory: {agents_dir}")
    for name in sorted(FORBIDDEN_ROOT_ENTRIES):
        ensure(not (repo_root / name).exists(), f"{repo_root / name}: forbidden at hub root")
    discovered = {path.name: path for path in agents_dir.iterdir() if path.is_dir() and not path.name.startswith(".")}
    ensure(discovered, f"{agents_dir}: at least one agent directory is required")
    ensure(set(discovered) == set(registry), f"{agents_dir}: directory set must match agents.toml registry")

    for agent_id, agent_dir in sorted(discovered.items()):
        ensure(registry[agent_id] == str(agent_dir.relative_to(repo_root)), f"{workspace_config}: path for {agent_id} must match directory")
        validate_agent(agent_dir, context_dir_name)


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
