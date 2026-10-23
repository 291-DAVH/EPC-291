# ADR-0005: Private material lives in an ignored `local/` folder

Status: Proposed. Date: 2026-10-23.

## Context
Standards (copyrighted), third-party reports, client documents, demo data and archived legacy folders must never be versioned or pushed, yet they must sit next to the code for convenience. Today they are four sibling folders at the repository root, which clutters it.

## Decision
- One git-ignored folder: `local/` with `dev-knowledge/`, `legacy/`, `projects-demo/` and `projects/<client>/`.
- The ignore rule is a single line (`/local/`); the pre-commit hook refuses anything under it; CI refuses PDF/DWG.
- The project skeleton (formerly `projects/_template`) moves to `management/templates/project-skeleton/`, versioned.
- Real client projects live in their own repositories; they may be cloned under `local/projects/`.

## Consequences
- (+) A clean root and one obvious place for everything that is not ours to publish.
- (-) Scripts and launch files that point to the old folder names must be updated (phase 2).
