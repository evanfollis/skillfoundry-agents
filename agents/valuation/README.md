# Valuation Agent

`valuation` compares predicted value against observed outcomes and sharpens what Skillfoundry should build next.

## Files

- `agent.toml`: agent manifest owned by the hub.
- `context/`: reserved mount path for the valuation context lineage checkout.
- `runtime.profiles = ["valuation"]`: declarative role-profile stack for this agent.
- `[projection]`: deterministic targets for writing resolved profile artifacts into the context repo.
