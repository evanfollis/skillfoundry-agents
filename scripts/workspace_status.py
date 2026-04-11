#!/usr/bin/env python3
"""Print workspace status by connecting agent registry to harness validation."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLFOUNDRY_ROOT = Path("/opt/projects/skillfoundry")


def load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text())


def _file_age_days(repo_root: Path, relative_path: str) -> int | None:
    """Return days since last git commit touching this file, or None if unknown."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "log", "-1", "--format=%aI", "--", relative_path],
        capture_output=True, text=True, check=False,
    )
    date_str = result.stdout.strip()
    if not date_str:
        return None
    try:
        committed = datetime.fromisoformat(date_str)
        now = datetime.now(timezone.utc)
        return (now - committed).days
    except ValueError:
        return None


def main() -> int:
    # Load agent registry
    agents_config = load_toml(REPO_ROOT / "agents.toml")
    agent_entries = agents_config.get("agents", [])

    if not agent_entries:
        print("No agents declared in agents.toml")
        return 1

    # Import harness (must be available in the active venv)
    try:
        from skillfoundry_harness import Runtime
        from skillfoundry_harness.validation import validate_context_repo, ValidationError
    except ImportError:
        print("ERROR: skillfoundry_harness not importable. Run from the harness venv.", file=sys.stderr)
        return 1

    print(f"Workspace: {agents_config.get('workspace_name', '?')}")
    print(f"Agents: {len(agent_entries)}")
    print("=" * 72)

    errors = 0
    for entry in agent_entries:
        agent_id = entry["agent_id"]
        agent_path = entry["path"]

        # Load agent.toml
        agent_toml_path = REPO_ROOT / agent_path / "agent.toml"
        if not agent_toml_path.exists():
            print(f"\n{agent_id}: MISSING agent.toml at {agent_toml_path}")
            errors += 1
            continue

        agent_config = load_toml(agent_toml_path)
        name = agent_config.get("name", "?")
        role = agent_config.get("role", "?")
        status = agent_config.get("status", "?")

        # Resolve context repo
        context_repo_path = SKILLFOUNDRY_ROOT / f"skillfoundry-{agent_id}-context"

        print(f"\n{agent_id}")
        print(f"  name:    {name}")
        print(f"  role:    {role}")
        print(f"  status:  {status}")
        print(f"  context: {context_repo_path}")

        # Validate via harness
        if not context_repo_path.is_dir():
            print(f"  validation: FAIL - context repo not found")
            errors += 1
            continue

        try:
            results = validate_context_repo(context_repo_path)
            print(f"  validation: PASS ({len(results)} check(s))")
        except (ValidationError, Exception) as exc:
            print(f"  validation: FAIL - {exc}")
            errors += 1
            continue

        # Frontdoor pinned paths + staleness
        try:
            rt = Runtime.open(context_repo_path)
            snapshot = rt.frontdoor_snapshot(max_chars=0)
            pinned = [p["path"] for p in snapshot.get("pinned", [])]
            if pinned:
                print(f"  frontdoor pinned:")
                for p in pinned:
                    age = _file_age_days(context_repo_path, p)
                    tag = f" ({age}d ago)" if age is not None else ""
                    stale = " ⚠ STALE" if age is not None and age > 14 else ""
                    print(f"    - {p}{tag}{stale}")
            else:
                print(f"  frontdoor pinned: (none)")
        except Exception as exc:
            print(f"  frontdoor: ERROR - {exc}")

    print("\n" + "=" * 72)
    if errors:
        print(f"{errors} agent(s) with issues")
        return 1
    else:
        print("All agents OK")
        return 0


if __name__ == "__main__":
    sys.exit(main())
