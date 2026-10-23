# ADR-0003: Engine as pure libraries, Claude layer as thin packaging

Status: Proposed. Date: 2026-10-23.

## Context
Today each hub plugin mixes three things: the Python code (calculation, drawings), the Claude packaging (manifest, skills) and data. The same engine must serve three clients: Claude Code skills, the backend API, and later the desktop app. Claude Code's own plugin layout is: `.claude-plugin/plugin.json` (optional manifest), `skills/<name>/SKILL.md`, `agents/*.md`, `hooks/hooks.json`, `.mcp.json`, `bin/` at the plugin root; a marketplace is a repository with `.claude-plugin/marketplace.json` listing plugins. Plugin `name` is kebab-case and namespaces its components; names starting with `claude-` or `anthropic-` are reserved. `claude plugin validate` is the authoritative check.

## Decision
- `engine/` holds the engineering code as installable Python packages with no web and no Claude dependency (`calc`, `drawing`, `rules`, `standards`, `documents`).
- `claude/plugins/<id>/` holds only packaging: manifest, wiring scripts that call `engine/`, MCP servers where needed. Skills stay in `claude/skills/` and agents in `claude/agents/`; the build copies them into the plugin package so the shipped layout is the official one. Plugins govern their skills (the plugin copy wins on duplicates; production builds fail on conflicts).
- `claude/marketplace/.claude-plugin/marketplace.json` lists our plugins so they can be installed with the standard plugin commands.
- CI runs `claude plugin validate --strict` on every built plugin.
- Plugin names avoid the reserved prefixes.

## Consequences
- (+) One engine, three consumers; engine tests run without Claude.
- (+) Packaging errors are caught by the official validator.
- (-) The migration touches every plugin (phases 3 and 4 of the plan).
- (-) Two representations of a plugin (source and built package); the build step must stay trivial.

Source: [Claude Code plugin manifest reference](https://code.claude.com/docs/en/plugins-reference).
