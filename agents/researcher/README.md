# Researcher Agent

`researcher` is the first scaffolded Skillfoundry agent in the hub.

Its purpose is to gather external and internal context, synthesize findings, and
materialize structured research outputs for downstream agents or humans.

## Files

- `agent.toml`: agent manifest owned by the hub.
- `context/`: reserved path for the agent's context repo submodule.

`agent.toml` is the authority for this agent's metadata. The workspace registry only
tracks that this agent exists and where it is mounted.

## Next Step

Attach the agent's context repo as a submodule:

```bash
git submodule add <context-repo-url-or-path> agents/researcher/context
```
