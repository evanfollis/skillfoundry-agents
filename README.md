# skillfoundry-agents

`skillfoundry-agents` is the coordination hub for Skillfoundry agents.

This repo tracks which agents exist, where their context repos live, and how the
workspace is organized. Each agent owns a `context/` repository, typically mounted
as a git submodule under `agents/<agent>/context`.

The hub is intentionally narrow:

- `agents.toml` is the workspace index and topology contract.
- `agents/<agent>/agent.toml` is the source of truth for agent metadata.
- `agents/<agent>/context/` is the source of truth for evolving agent state.

## Scope

- Agent registry and manifests.
- Workspace topology for agent context repos.
- Shared coordination docs and conventions.
- Light validation that the hub structure is coherent.

## Non-goals

- Canonical context schema ownership.
- Runtime implementation.
- Long-lived agent memory or bundles stored at the hub root.

## Repository Layout

- `agents.toml`: workspace-level hub configuration.
- `agents/`: one directory per agent.
- `agents/<agent>/agent.toml`: manifest for that agent.
- `agents/<agent>/context/`: git submodule to the agent's context repo.
- `tests/`: workspace validation tests and fixtures.
- `docs/`: workspace conventions.
- `scripts/`: hub validation entrypoints.

## Local Validation

```bash
python3.12 scripts/check_workspace.py
python3.12 -m unittest discover -s tests
```
