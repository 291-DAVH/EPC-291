# marketplace

`marketplace.template.json` holds the marketplace identity (name, owner, description). `tools/build/epc_build.py marketplace` generates the real marketplace in `dist/marketplace/` (git-ignored): every active plugin assembled in Claude Code's official layout plus `.claude-plugin/marketplace.json`. Plugins with `status: pending` are skipped.

Install from the repository once the generated marketplace is published:

```
/plugin marketplace add 291-DAVH/EPC-291
/plugin install sld --marketplace 291-DAVH/EPC-291
```
Until then, test locally with `claude plugin validate --strict dist/marketplace` or `claude --plugin-dir dist/marketplace/plugins/<id>`.
