# Contributing

1. **Branches.** Never commit on `main` or `dev`. Branch from `dev`: `feature/<topic>`, `fix/<topic>` or `chore/<topic>`; merge back with `--no-ff`. Details: [docs/BRANCHING.md](docs/BRANCHING.md).
2. **Hook.** Enable it once per clone: `git config core.hooksPath platform/tools/hooks`. It refuses direct commits on `main`/`dev`, PDF/DWG files, files over 5 MB and anything from `local/dev-knowledge/`, `_legacy/` or `local/projects-demo/`.
3. **Where things live.** Engineering code only in `engine/<area>/src/`; plugins (packaging) in `claude/plugins/<id>/`; skills in `claude/skills/<id>/`; agents in `claude/agents/`. Plugins govern their skills.
4. **Before merging anything**: `python tools/ci/run_gate.py` (full test battery). After replacing a plugin or skill, from `platform/`:
   ```
   python tools/ci/check_skill_conflicts.py --env production
   python tools/build/epc_build.py registry
   (cd backend && python -m unittest discover -s tests -t . && lint-imports)
   ```
5. **Versions.** Bump `version` in the plugin's `plugin.json` and add a line to [CHANGELOG.md](CHANGELOG.md) for every behavior change.
6. **Language.** Product content (code, schemas, ids, templates, prompts) is English. Claude explains to the user in Spanish.
7. **Commits.** Conventional Commits: `feat(scope): ...`, `fix(scope): ...`, `docs: ...`, `chore: ...`.
8. **Private material.** Standards, third-party reports and client data never enter the repository.
