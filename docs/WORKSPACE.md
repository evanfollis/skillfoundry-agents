# Workspace Layout

`skillfoundry-agents` is the hub. Each agent lives under `agents/<agent>/` and should
have:

- `agent.toml`: manifest for that agent.
- `context/`: local mount point for a checkout of the agent's git-backed context lineage.

## Sources Of Truth

- `agents.toml` is the global index of `agent_id -> path`.
- `agent.toml` owns the agent's role, lifecycle status, and purpose.
- `profiles/<profile>/profile.toml` owns reusable role overlays.
- the mounted `context/` checkout owns the agent's actual working state.

## Recommended Layout

```text
profiles/
  researcher/
    profile.toml
agents/
  researcher/
    agent.toml
    context/   # mounted checkout, usually ignored by the hub repo
```

## Creating A New Agent

1. Create `agents/<agent>/`.
2. Pick one or more existing profiles from `profiles/` and reference them from `agents/<agent>/agent.toml`.
3. Add `agents/<agent>/agent.toml`.
4. Materialize or mount a context lineage checkout at `agents/<agent>/context`.
5. Update `agents.toml` only if workspace-wide defaults change.

## Lifecycle Rule

- `planned` agents may omit the mounted `context/` checkout temporarily.
- `active` and `paused` agents must have a valid git-backed `context/` checkout.
- Hub-level validation should fail if context data appears directly under
  `agents/<agent>/` instead of inside `context/`.

## Parallel Work Rule

Parallel agent work should happen through branch or worktree isolation inside the
agent's `context/` repo. The hub should not become a shared mutable scratchpad.

## Profile Rule

Profiles are reusable overlays, not runtime code and not live agent state.

- `runtime.profiles` in `agent.toml` declares the requested profile stack.
- `runtime.skills` may declare named skill overlays when a workspace uses them.
- Profiles may extend other profiles.
- Profile resolution is deterministic and should be treated as a build-time or
  pre-run input into the agent's context front door, not as hidden runtime magic.

## Projection Rule

Profiles do not matter until they become concrete seed artifacts for an agent's
actual context repo.

- `projection.memory_profile_path` declares where the resolved markdown profile should
  be written inside the context repo's `memory/` root.
- `projection.bundle_profile_path` declares where the resolved profile bundle should
  be written inside the context repo's `bundles/` root.
- `projection.require_frontdoor_pin = true` means the target memory file must already
  be pinned by the context repo's front door before projection is allowed.

Projection is explicit and deterministic. The hub resolves profiles; the context repo
remains the live mind.

## Current Scaffold

The hub currently includes one agent:

- `researcher`
- `builder`

It also includes a reusable initial profile set for the first business system:

- `researcher`
- `designer`
- `builder`
- `infra_auth`
- `pricing`
- `growth`
- `valuation`

Their manifests live at:

- `agents/researcher/agent.toml`
- `agents/builder/agent.toml`

## Example Local-First Commands

```bash
skillfoundry init-context agents/<agent>/context --agent-id <agent> --name "<Agent> Context"
skillfoundry fork-context /path/to/seed-lineage agents/<agent>/context --agent-id <agent> --name "<Agent> Context"
```

The harness should then be pointed at `agents/<agent>/context`, not at the hub root.
