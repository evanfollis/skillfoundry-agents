# Architecture

`skillfoundry-agents` is the declarative coordination hub for the Skillfoundry
federation. `agents.toml` indexes agents; `agents/<id>/agent.toml` owns each
agent declaration; `profiles/` supplies deterministic overlays. The Python in
`scripts/` validates and projects those declarations but does not execute agent
work.

The hub deliberately does not own durable context or runtime semantics.
Context is mounted under the gitignored `agents/<id>/context/` path on operator
hosts and remains authoritative in the corresponding
`skillfoundry-<id>-context` repository. `skillfoundry-harness` owns execution
and context-repository validation.

CI runs declaration mode because clean checkouts do not contain the gitignored
mounts. Operators use `make operator-check` to verify mount liveness. The dirty
host-local edit to `scripts/workspace_status.py` predates the July 2026
migration and remains principal-owned.

## July 2026 transition exception

This repository declares `agentic_risk = "agentic"` but the host session fabric
does not yet provide project-scoped non-root identities, default-deny
filesystem/network isolation, or brokered task credentials. The supervisor
owns that bounded host-wide gap under ADR-0050. Prompt/instruction baselines
for the existing agent declarations also remain to be established under
ADR-0039; until then the central inventory must keep this repo `migrating`.
