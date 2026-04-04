# Principles

## The Hub Coordinates, It Does Not Govern Canonical Semantics

This repo should know which agents exist and where their context repos live. It should
not become a second home for the harness contract.

## Each Agent Owns Its Context Repo

An agent's evolving memory and bundles belong inside its `context/` repo, not scattered
through the hub.

## The Registry Should Not Compete With The Manifest

`agents.toml` should answer "which agents exist and where are they mounted?" Agent
identity, role, and lifecycle state belong in the per-agent manifest.

## Submodules Are A Deliberate Tradeoff

Using submodules buys independent history and pinning. Accept the operational cost and
make the workflow explicit rather than hand-waving it away.

## Shared State Must Be Intentional

Cross-agent coordination should happen through explicit shared configuration or harness
APIs, not by informal edits across context repos.
