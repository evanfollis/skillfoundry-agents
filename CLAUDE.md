# Skillfoundry Agents

## What This Is
Coordination hub for Skillfoundry agents. Tracks agent registries, profiles, and workspace organization.

## Key Files
- `agents.toml` — Agent registry
- `AGENTS.md` — Agent documentation

## Active Decisions

- **agents.toml is the registry of record.** Agent existence is defined there. AGENTS.md is documentation, not config.
- **Harness is the runtime.** This repo coordinates; it doesn't execute. Execution logic belongs in skillfoundry-harness.

## Related Repos
- `skillfoundry-harness` — The runtime that executes these agents
- `skillfoundry-*-context` — Per-agent context lineages
