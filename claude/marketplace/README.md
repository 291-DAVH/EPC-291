# marketplace

`marketplace.template.json` holds the marketplace identity (name, owner, description). `platform/tools/build/epc_build.py marketplace` generates the real marketplace in `platform/dist/marketplace/` (git-ignored): every active plugin assembled in Claude Code's official layout plus `.claude-plugin/marketplace.json`. Plugins with `status: pending` are skipped.

Install from the repository once the generated marketplace is published:

```
/plugin marketplace add 291-DAVH/EPC-291
/plugin install sld --marketplace 291-DAVH/EPC-291
```
Until then, test locally with `claude plugin validate --strict platform/dist/marketplace` or `claude --plugin-dir platform/dist/marketplace/plugins/<id>`.
