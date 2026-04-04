# Principles

## The Hub Coordinates, It Does Not Govern Canonical Semantics

This repo should know which agents exist and where their context repos live. It should
not become a second home for the harness contract.

## Each Agent Owns Its Context Repo

An agent's evolving memory and bundles belong inside its `context/` repo, not scattered
through the hub.

The context repo is the primary canonical artifact for that agent. Profiles and skills
shape behavior around it, but they do not replace it.

## The Registry Should Not Compete With The Manifest

`agents.toml` should answer "which agents exist and where are they mounted?" Agent
identity, role, and lifecycle state belong in the per-agent manifest.

## Profiles Are Reusable Overlays, Not Runtime Law

Reusable role profiles belong in the hub because they help shape families of agents.
They should remain declarative, composable, and subordinate to the harness contract.

## Context Mounts Are Local-First

An agent's `context/` path is a mount point for a git-backed context lineage. It may be
populated by a local clone, a worktree, or a submodule, but the hub should not treat any
one attachment mechanism as the definition of the architecture.

## Shared State Must Be Intentional

Cross-agent coordination should happen through explicit shared configuration or harness
APIs, not by informal edits across context repos.
