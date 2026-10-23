# Contributing

1. **Branches.** Never commit on `main` or `dev`. Branch from `dev`: `feature/<topic>`, `fix/<topic>` or `chore/<topic>`; merge back with `--no-ff`. Details: [docs/BRANCHING.md](docs/BRANCHING.md).
2. **Hook.** Enable it once per clone: `git config core.hooksPath platform/tools/hooks`. It refuses direct commits on `main`/`dev`, PDF/DWG files, files over 5 MB and anything from `dev-knowledge/`, `_legacy/` or `projects-demo/`.
3. **Where things live.** Plugins only in `platform/hub/<id>/`; skills only in `platform/skills/<id>/`. Plugins govern their skills.
4. **After replacing a plugin or skill**, from `platform/`:
   ```
   python tools/ci/check_skill_conflicts.py --env production
   python tools/build/epc_build.py registry
   python -m unittest apps.api.test_projects apps.api.test_app
   ```
5. **Versions.** Bump `version` in the plugin's `plugin.json` and add a line to [CHANGELOG.md](CHANGELOG.md) for every behavior change.
6. **Language.** Product content (code, schemas, ids, templates, prompts) is English. Claude explains to the user in Spanish.
7. **Commits.** Conventional Commits: `feat(scope): ...`, `fix(scope): ...`, `docs: ...`, `chore: ...`.
8. **Private material.** Standards, third-party reports and client data never enter the repository.
