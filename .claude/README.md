# .claude

The only Claude Code settings folder of the repository: it configures Claude Code while **developing EPC-291** (not the product's plugins, which live in `claude/`).

- `launch.json` (git-ignored, machine-specific): dev servers `epc-api`, `epc-api-admin`, `epc-web`, `epc-console`; reads `.env.demo` / `.env.admin` from the repository root.
- Future: shared `settings.json`, development agents and commands (add them here and un-ignore them in `.gitignore`).
