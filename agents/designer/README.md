# Designer Agent

`designer` converts validated bottlenecks into explicit product and workflow specs.

## Files

- `agent.toml`: agent manifest owned by the hub.
- `context/`: reserved mount path for the designer context lineage checkout.
- `runtime.profiles = ["designer"]`: declarative role-profile stack for this agent.
- `[projection]`: deterministic targets for writing resolved profile artifacts into the context repo.
