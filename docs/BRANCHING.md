# Branching policy

| Branch | Purpose | Who writes to it |
|---|---|---|
| `main` | **Stable.** Only code that passed the release checklist. Every release is tagged `vX.Y.Z`. | Merges from `dev` (or `hotfix/*`) only |
| `dev` | **Integration.** Everything that is finished is joined and tested here before going to `main`. | Merges from `feature/*`, `fix/*` only |
| `feature/<topic>` | One piece of work (a plugin, the web app, the rules engine...). Branched from `dev`. | The author |
| `fix/<topic>` | Bug fix not yet in `main`. Branched from `dev`. | The author |
| `hotfix/<topic>` | Urgent fix of `main`. Branched from `main`, merged to `main` **and** `dev`. | The author |

```
main      o───────────────────────────────o  v0.1.0
           \                             /
dev         o──●──────●─────●─────●─────●
                \    /       \   /
feature/a        o──o         \ /
feature/b                      o
```

## Rules
1. No direct commits on `main` or `dev` (the pre-commit hook refuses them). Work on a branch; merge with `--no-ff` so each feature stays visible in history.
2. A feature branch is merged into `dev` only when its tests pass:
   ```
   python tools/build/epc_build.py registry
   python tools/ci/check_skill_conflicts.py --env production
   python -m unittest apps.api.test_projects apps.api.test_app      # from platform/
   ```
3. `dev` goes to `main` when the whole suite is green and the checklist is done: changelog updated, version bumped in the affected `plugin.json`, no draft rules promoted by mistake, no PDF/DWG/dev-knowledge content staged.
4. Commit messages follow Conventional Commits: `feat(scope): ...`, `fix(scope): ...`, `docs: ...`, `chore: ...`.
5. Never push `dev-knowledge/`, `_legacy/`, client projects or copyrighted files. They are listed in `.gitignore`; the hook adds a second barrier.

## Override (rare)
`ALLOW_PROTECTED=1 git commit ...` is accepted by the hook for the initial baseline or an emergency `hotfix`.

## Remote
The repository has an `origin` remote. Nothing is pushed automatically. Pushing `main` or `dev` is an explicit decision of the owner.
