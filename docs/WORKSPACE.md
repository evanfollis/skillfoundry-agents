# Workspace Layout

`skillfoundry-agents` is the hub. Each agent lives under `agents/<agent>/` and should
have:

- `agent.toml`: manifest for that agent.
- `context/`: git submodule pointing at the agent's context repository.

## Sources Of Truth

- `agents.toml` is the global index of `agent_id -> path`.
- `agent.toml` owns the agent's role, lifecycle status, and purpose.
- `context/` owns the agent's actual working state.

## Recommended Layout

```text
agents/
  researcher/
    agent.toml
    context/   # git submodule
```

## Creating A New Agent

1. Create `agents/<agent>/`.
2. Add `agents/<agent>/agent.toml`.
3. Add the context repo as a submodule at `agents/<agent>/context`.
4. Update `agents.toml` only if workspace-wide defaults change.

## Lifecycle Rule

- `planned` agents may omit the `context/` submodule temporarily.
- `active` and `paused` agents must have a checked-out `context/` submodule.
- Hub-level validation should fail if context data appears directly under
  `agents/<agent>/` instead of inside `context/`.

## Parallel Work Rule

Parallel agent work should happen through branch or worktree isolation inside the
agent's `context/` repo. The hub should not become a shared mutable scratchpad.

## Current Scaffold

The hub currently includes one agent:

- `researcher`

Its manifest lives at `agents/researcher/agent.toml`. The `context/` submodule has not
been attached yet, because that requires the concrete context repo path or remote.

## Example Submodule Command

```bash
git submodule add git@github.com:YOUR_ORG/YOUR_CONTEXT_REPO.git agents/<agent>/context
```

The harness should then be pointed at `agents/<agent>/context`, not at the hub root.
