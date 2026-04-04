# Researcher Agent

`researcher` is the first scaffolded Skillfoundry agent in the hub.

Its purpose is to gather external and internal context, synthesize findings, and
materialize structured research outputs for downstream agents or humans.

## Files

- `agent.toml`: agent manifest owned by the hub.
- `context/`: reserved mount path for the agent's context lineage checkout.
- `runtime.profiles = ["researcher"]`: declarative role-profile stack for this agent.
- `[projection]`: deterministic targets for writing resolved profile artifacts into the context repo.

`agent.toml` is the authority for this agent's metadata. The workspace registry only
tracks that this agent exists and where it is mounted.

## Local Mount

When this agent is active locally, mount or create its context lineage at `context/`.
To refresh the projected role seed artifacts into that checkout:

```bash
python3.12 scripts/project_agent.py agents/researcher/agent.toml agents/researcher/context
```
