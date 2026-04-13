# skillfoundry-agents

`skillfoundry-agents` is the coordination hub for Skillfoundry agents.

This repo tracks which agents exist, where their context repos live, and how the
workspace is organized. Each agent owns a `context/` repository, mounted locally at
`agents/<agent>/context` as a checkout of that agent's git-backed context lineage.
That lineage may remain local, may later be published to a remote, and may be mounted
via a plain clone, a worktree, or a submodule. The mount path matters; the transport
mechanism does not.

The hub is intentionally narrow:

- `agents.toml` is the workspace index and topology contract.
- `agents/<agent>/agent.toml` is the source of truth for agent metadata.
- `profiles/<profile>/profile.toml` defines reusable role/profile overlays.
- `runtime.skills` in `agent.toml` may declare thin runtime overlays when needed.
- `agents/<agent>/context/` is the mounted checkout of the source of truth for evolving
  agent state.

The current default operating stack for Skillfoundry includes these long-lived agent
lineages:

- `researcher`
- `builder`
- `designer`
- `pricing`
- `growth`
- `valuation`

These roles now support a staged commercial controller above the harness:

- Stage 1 uses `CriticalAssumption`, `Probe`, `Evidence`, and `Decision`.
- Stage 2 may later promote validated lanes into `Opportunity`, `Offering`,
  `PortfolioDecision`, and `PortfolioSnapshot`.
- The harness still owns execution semantics; the controller owns commercial choice.

## Scope

- Agent registry and manifests.
- Reusable role profile overlays and deterministic profile resolution.
- Projection of resolved profiles into concrete context-repo seed artifacts.
- Workspace topology for mounted agent context lineages.
- Shared coordination docs and conventions.
- Light validation that the hub structure is coherent.

## Non-goals

- Canonical context schema ownership.
- Runtime implementation.
- Long-lived agent memory or bundles stored at the hub root.

## Repository Layout

- `agents.toml`: workspace-level hub configuration.
- `profiles/`: reusable role/profile definitions.
- `agents/`: one directory per agent.
- `agents/<agent>/agent.toml`: manifest for that agent.
- `agents/<agent>/context/`: local mount point for the agent's context lineage checkout.
- `tests/`: workspace validation tests and fixtures.
- `docs/`: workspace conventions.
- `scripts/`: hub validation entrypoints.

## Local Validation

```bash
python3.12 scripts/check_workspace.py
python3.12 scripts/resolve_profiles.py agents/researcher/agent.toml
python3.12 scripts/resolve_profiles.py agents/builder/agent.toml
python3.12 scripts/project_agent.py agents/researcher/agent.toml /path/to/context-repo
python3.12 -m unittest discover -s tests
```
