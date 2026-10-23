# skills — single place for all skills

One folder per skill: `skills/<skill-id>/SKILL.md` (+ `references/`, `templates/`, `scripts/` only if the skill needs them).

## Governance (plugins always rule)
1. A skill has **exactly one owner plugin** (`role: owner` in that plugin's `plugin.json`). Other plugins may use it as `consumer`.
2. A skill that no plugin lists is **inactive**: it is not built, not packaged and not offered to the agent.
3. Plugin settings win over the skill's own defaults (`overrides`: inputs, outputs, gates, language, jurisdiction).
4. Version, permissions, entitlement (subscription) and dependencies are decided by the plugin, never by the skill.
5. Scripts and data belong to plugins (`hub/<id>/`); a skill calls them through its plugin and never carries its own copy.
6. Skill ids are in English (`generate-specification`, not `generar-pliego`). Skill text is English; the agent answers the user in Spanish.

## Duplicates: the plugin copy governs, and I warn you
If the same skill exists in `skills/` and inside a plugin (`hub/<plugin>/skills/<id>/`), the **plugin copy governs**.
`tools/ci/check_skill_conflicts.py` reports every case (identical or different content):
- development: WARNING (work continues);
- production build (`--env production`): ERROR, the build is blocked until only one copy remains.
It also reports a skill inside two plugins, orphan skills and skills a plugin lists but that do not exist.

## Build
`tools/build` assembles each plugin package by copying the skills it lists from `skills/` into the package, so Claude Code still finds `skills/` inside the `.plugin`. Never edit the copies inside a built package.
