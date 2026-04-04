# Agents Directory

Create one directory per agent under this path.

Each agent directory should contain:

- `agent.toml`
- `context/` as a mounted checkout of the agent's context lineage

The directory itself should not accumulate `bundles/`, `memory/`, `artifacts/`, or
`runs/`. Those belong inside `context/`.

No agent context data should be stored directly at the hub root.
