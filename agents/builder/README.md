# Builder Agent

`builder` turns validated briefs into deployable MCP servers and related launch-ready
artifacts.

## Files

- `agent.toml`: agent manifest owned by the hub.
- `context/`: reserved mount path for the builder context lineage checkout.
- `runtime.profiles = ["builder"]`: declarative role-profile stack for this agent.
- `[projection]`: deterministic targets for writing resolved profile artifacts into the context repo.

## Local Mount

When this agent is active locally, mount or create its context lineage at `context/`.
To refresh the projected role seed artifacts into that checkout:

```bash
python3.12 scripts/project_agent.py agents/builder/agent.toml agents/builder/context
```
