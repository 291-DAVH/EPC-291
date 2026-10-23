# ADR-0001: Monorepo with a modular monolith backend

Status: Proposed. Date: 2026-10-23.

## Context
The product has a web front, a Python backend, engineering libraries, a Claude layer, documentation and planning. They evolve together (a deliverable type touches the engine, the API, the UI and a skill). A team of one to a few people cannot afford the operational cost of many repositories or microservices, but the codebase is meant to grow large and stay navigable. Common guidance for monorepos is to separate deployable `apps` from shared `packages`, to start with few packages rather than many, and to enforce consistency in CI. For Python backends, a modular monolith with one package per bounded context, a small public facade per module and import contracts (import-linter) keeps boundaries without distribution costs.

## Decision
- One repository (`EPC-291`) with top-level folders per concern (see [target architecture](../README.md)).
- The backend is one FastAPI deployable split into modules (bounded contexts). Each module exposes only `public.py`; other modules import nothing else. An import-linter contract and architecture tests enforce it in CI.
- Start with few packages (`engine/*` as 5 packages, not 20). Extract a module to its own service only when it needs independent scaling or deployment.
- Folders are organized by capability (feature), not by technical layer, at the top of each module.

## Consequences
- (+) One change = one branch/PR across front, back, engine and skills; shared tooling and CI.
- (+) Clear ownership and a path to extract services later.
- (-) Needs discipline: boundary violations must fail CI, not code review.
- (-) A larger repository: use path-based CI and caching.

Sources: [Python monorepos guide](https://dev.to/ctrix/mastering-python-monorepos-a-practical-guide-2b4), [vertical monorepo for FastAPI](https://sqr-075.lsst.io/), [Module boundary enforcement](https://platform-django-template.readthedocs.io/en/latest/4-guides/module-boundary-enforcement.html), [Bounded contexts in a modular monolith](https://milanjovanovic.tech/blog/module-boundaries-bounded-contexts.md).
