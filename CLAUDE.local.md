# Workspace-local Config

This file is gitignored at the org level for some teams; in this workspace it IS committed so future
Claude Code sessions and teammates pick up the same Linear/GitHub bindings without prompting.

## Linear

- **Team:** `Sapphire_Agentic_Team`
- **Project:** `SDD-Cookbook-demo`

All spec tickets for this workspace go in that team + project. Default ticket status when a spec is
ready for Gate 1: `Spec Ready`.

## GitHub

- **Repo:** `anshul-expoAI/claude-cookbook-demo`
- **Default branch:** `main`
- **Branch policy:** `main` is used for the initial bootstrap commit (specs scaffolding). All
  subsequent specs and feature work go through feature branches and PRs.

## Spec file conventions

- Project-level overview: `specs/PROJECT.md`
- Technical spec: `specs/TECH_SPEC.md`
- Cycle plans: `specs/cycles/CYCLE_*.md`
- Task breakdown: `specs/cycles/CYCLE_*_TASKS.md`
- Feature folders: `specs/features/<slug>/` (with `memory/` + `status.yaml`)
