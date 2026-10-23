# planning

Software planning for **EPC-291 during development**. This folder is not shipped to clients. It uses the same schemas as the product's own project-management module (`management/schemas/`), so we plan the product with the data model we sell.

| Folder / file | Content |
|---|---|
| [vision.md](vision.md) | Product vision, users, value, scope and non-goals |
| [roadmap/ROADMAP.md](roadmap/ROADMAP.md) | Now / Next / Later and milestones |
| [prd/](prd/README.md) | Product requirement documents, one per capability |
| [backlog/](backlog/) | `epics/` (EP-nnn), `stories/` (US-nnnn), `bugs/`, `spikes/` |
| [sprints/](sprints/README.md) | `SPRINT-NN/plan.md`, `review.md`, `retro.md` |
| [releases/](releases/) | Release notes per version |
| [risks/risk-register.md](risks/risk-register.md) | Risks with probability, impact and response |
| [templates/](templates/) | PRD, epic, story, sprint plan, retrospective |
| [BOARD.md](BOARD.md) | **Generated** board: backlog by status, sprint view, epic progress |

## How it works
1. A need becomes a **PRD** (why, who, scope, success metrics). A PRD is split into **epics**; an epic into **user stories** with acceptance criteria.
2. Every epic and story is a Markdown file with front matter (`id`, `type`, `title`, `epic`, `status`, `priority`, `estimate`, `sprint`).
3. Status values: `backlog` -> `ready` -> `in-progress` -> `review` -> `done` (or `blocked`). Priorities: `P1` must, `P2` should, `P3` could. Estimates are story points (1, 2, 3, 5, 8, 13).
4. A sprint is two weeks. Planning moves stories into `SPRINT-NN` by editing `sprint:` in the story.
5. Regenerate the board after any change:
   ```
   python tools/planning/board.py
   ```
6. Branches follow `docs/BRANCHING.md`. Each story is delivered through a `feature/*` branch whose name carries the story id (for example `feature/us-0009-validate-771`).

## Definition of ready
Acceptance criteria written, estimate given, dependencies known, no open question on scope.

## Definition of done
Code merged into `dev` through a branch, tests green, registry and skill checks green, documentation and CHANGELOG updated, nothing private committed.
