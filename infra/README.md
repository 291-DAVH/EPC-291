# infra

```
docker/    backend.Dockerfile, frontend.Dockerfile (nginx), nginx.conf
compose/   compose.yml: db (PostgreSQL 16) -> migrate (alembic upgrade head) -> backend -> frontend
```
CI lives in `.github/workflows/ci.yml` (gate on Python + Node, migrations against a real PostgreSQL, image builds).

## Local stack
```
copy infra\compose\.env.example infra\compose\.env       (set POSTGRES_PASSWORD)
docker compose -f infra/compose/compose.yml --env-file infra/compose/.env up --build
```
Customer app http://localhost:8080, console http://localhost:8081 (bound to localhost). The stack runs with accounts (`EPC_AUTH=required`): create the first staff account once, then sign in on either address and create organizations in the console (*Organizaciones*):
```
docker compose -f infra/compose/compose.yml --env-file infra/compose/.env run --rm backend python -m epc.modules.identity.cli create-admin --email you@office.com --name "Your Name"
```

## Notes
- Project folders go to the `projects` volume; PostgreSQL holds the accounts (users, organizations, sessions, invitations; see `database/README.md` and ADR-0009). Back up both.
- Images never contain `local/` (see `.dockerignore`): no study material, no client data.
- Not yet: Kubernetes/Helm, on-premise packaging, secrets management.
- The images could not be built in the development machine of this phase (no Docker there); CI builds them on every push, and `tools/ci/check_infra.py` validates the files statically.
