# Pricing Agent

`pricing` turns validated utility into pricing and packaging hypotheses that can be tested.

## Files

- `agent.toml`: agent manifest owned by the hub.
- `context/`: reserved mount path for the pricing context lineage checkout.
- `runtime.profiles = ["pricing"]`: declarative role-profile stack for this agent.
- `[projection]`: deterministic targets for writing resolved profile artifacts into the context repo.
