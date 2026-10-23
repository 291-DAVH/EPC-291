# Contributing

1. Plugins live only in `hub/<id>/`; skills only in `skills/<id>/`. Plugins govern their skills.
2. Replaced a plugin or skill? Run:
   ```
   python tools/ci/check_skill_conflicts.py --env production
   python tools/build/epc_build.py registry
   ```
3. Never commit PDF/DWG or anything from `dev-knowledge/`. Enable the hook: `git config core.hooksPath tools/hooks`.
4. Product content (code, schemas, ids, templates, prompts) is English. Claude explains to the user in Spanish.
5. Bump `version` in `plugin.json` and add a `CHANGELOG.md` line for every behavior change.
