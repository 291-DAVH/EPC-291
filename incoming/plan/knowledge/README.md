# What the module learns

Rules the module applies are kept here **as data**, each with where it comes from and whether the norm reviewer approved it (the same way the platform keeps norm data):

```
rules.json   [{"id": "...", "statement": "...", "value": ..., "unit": "...", "source": "book / standard, edition, section", "status": "pending|approved|rejected"}]
```

- The books, PDFs and drawings you study **never go in this folder** (copyright): they stay in `local/dev-knowledge/` of the repository, which git ignores.
- What goes here is what was **extracted** from them: the rule, its value and its source.
- Nothing in `core.py` carries a rule inline: it reads `rules.json`.
