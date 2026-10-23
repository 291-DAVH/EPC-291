# EPC-291

Automated EPC engineering framework built from plugins ("Lego"): calculation, drawings, documents, rules from standards, and a web app for end users. Code lives in [`platform/`](platform/README.md).

```
EPC-291/
├─ platform/        product source (hub of plugins, skills, core, apps, schemas, tools)        VERSIONED
├─ projects/_template/   project skeleton: workspace (editable) + deliverables (client-facing)  VERSIONED
├─ docs/            repository policies (branching)                                           VERSIONED
├─ dev-knowledge/   standards, third-party reports, study material                            PRIVATE, git-ignored
├─ projects-demo/   20 simulated projects for demos                                           git-ignored
├─ projects/<client>/  real projects (each has its own repository)                           git-ignored
└─ _legacy/         archived original folders and old repositories                            git-ignored
```

- Branches: `main` (stable) <- `dev` (integration) <- `feature/*`. See [docs/BRANCHING.md](docs/BRANCHING.md).
- Enable the safety hook after cloning: `git config core.hooksPath platform/tools/hooks`.
- Español: [platform/docs/README.es.md](platform/docs/README.es.md).
