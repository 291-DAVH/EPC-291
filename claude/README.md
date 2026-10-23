# claude

The AI layer of EPC-291: everything that is packaged for Claude. Engineering code stays in `platform/` for now and moves to `engine/` in phase 4; plugins then become thin wrappers.

| Folder | Content |
|---|---|
| [plugins/](plugins/README.md) | One folder per plugin: our `plugin.json`, code and data. `registry.json` is generated |
| [skills/](skills/README.md) | All skills (`<id>/SKILL.md`). Plugins govern them |
| [agents/](agents/) | Specialist agents (Markdown with front matter) referenced by plugins |
| [marketplace/](marketplace/README.md) | Template for the marketplace that ships these plugins |
| [mcp/](mcp/README.md) | MCP servers (planned: one per capability) |
| [prompts/](prompts/README.md) | Reusable prompts and style rules (planned) |
| [evals/](evals/README.md) | Evaluation cases per skill (planned) |

## Build and validate
```
platform\.venv\Scripts\python platform\tools\build\epc_build.py registry      # plugins + skills + agents consistency
platform\.venv\Scripts\python platform\tools\build\epc_build.py marketplace   # platform/dist/marketplace (git-ignored build output)
claude plugin validate --strict platform\dist\marketplace
```
`python tools/ci/run_gate.py` runs all of it, including the official validator on the marketplace and on every plugin.

## Rules
1. Plugins govern skills; a skill defined twice is a warning in development and an error in production builds.
2. Plugin names are kebab-case and must not start with `claude-` or `anthropic-` (reserved).
3. Nothing from `local/` and no PDF/DWG is ever packaged.
4. The end-user app never exposes this layer; it exists for the admin role and for developers.
