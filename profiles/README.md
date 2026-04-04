# Role Profiles

Profiles are reusable overlays for agents.

They are not harness primitives and they are not the agent's live mind. They exist so
multiple agent instances can start from a shared operational stance without hardcoding
business roles into `skillfoundry-harness`.

Each profile lives under `profiles/<profile_id>/profile.toml`.

## Merge Model

- Profiles may `extend` other profiles.
- Agent manifests request one or more profiles through `runtime.profiles`.
- Resolution is deterministic:
  - profile inheritance is resolved first
  - requested profiles are then merged in declared order
  - `persona.summary` is overwritten by the latest profile that sets it
  - list-valued fields are concatenated with stable de-duplication

## Current Shape

The current profile contract is intentionally small:

- `[persona]`
- `[frontdoor]`
- `[policy]`
- `[handoff]`

That is enough to shape front-door guidance and operating expectations without
turning the hub into a second runtime.
