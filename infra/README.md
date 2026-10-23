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
Customer app http://localhost:8080, console http://localhost:8081 (bound to localhost; start with `EPC_ROLE=admin` to use it).

## Notes
- The backend is still file-based: project folders go to the `projects` volume; the database is created and migrated but not read yet (see `database/README.md`).
- Images never contain `local/` (see `.dockerignore`): no study material, no client data.
- Not yet: Kubernetes/Helm, on-premise packaging, secrets management.
- The images could not be built in the development machine of this phase (no Docker there); CI builds them on every push, and `tools/ci/check_infra.py` validates the files statically.
