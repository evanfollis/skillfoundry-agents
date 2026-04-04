# AGENTS.md

## Mission

Maintain the hub that coordinates Skillfoundry agents and their context repos.

## Required Behaviors

- Keep the hub focused on manifests, topology, and coordination.
- Assume canonical validation rules come from `skillfoundry-harness`.
- Make context-mount expectations explicit in docs and checks.
- Preserve clear boundaries between hub metadata and per-agent context state.
- Keep `agents.toml` as an index, not a duplicate home for agent metadata.

## Editing Rules

- Do not add canonical context schemas or validators here.
- Do not store agent memory, bundles, or artifacts at the hub root.
- Do not blur the line between hub manifests and per-agent context configuration.
- Prefer explicit `agent.toml` metadata over duplicated hub registry fields.

## Review Standard

A hub change should answer:

- What agent or workspace topology changed?
- Does this belong in the hub or in an agent's `context/` repo?
- What context-lineage or manifest assumption does it introduce?
