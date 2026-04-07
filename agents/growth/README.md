# Growth Agent

`growth` prepares distribution, onboarding, and go-to-market artifacts for launched products.

## Files

- `agent.toml`: agent manifest owned by the hub.
- `context/`: reserved mount path for the growth context lineage checkout.
- `runtime.profiles = ["growth"]`: declarative role-profile stack for this agent.
- `[projection]`: deterministic targets for writing resolved profile artifacts into the context repo.
