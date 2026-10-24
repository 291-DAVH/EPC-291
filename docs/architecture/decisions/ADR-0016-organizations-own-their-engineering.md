# ADR-0016: Organizations do their own engineering; their data is their own

Status: Accepted. Date: 2026-10-24. Extends ADR-0013.

## Context
The platform is used by independent professionals and by professionals who belong to different organizations. An independent professional is an organization of one person. Each organization has its personnel, its clients (the owners of its projects) and the companies it issues documents in the name of, and it must never see anything of another organization. Until now only the platform's engineering team could open the engineering workspace and the master data, and those data were one shared set for the whole installation.

## Decision
- A project has an **owner organization** (the solution provider; `org` in the project file), a **client** (the owner of the work, chosen from the organization's client list) and an **engineering team** (the personnel of the organization, per discipline: who designs, checks and approves).
- Two new subjects in the permission matrix: `workspace` (engineering of the organization's own projects: Ingeniería, registers, reports, issuing) and `orgdata` (clients, issuing companies, personnel and logos). Individuals, company owners and administrators read and write both; company members work the projects and only read the organization's data; inspectors and auditors get neither; the technical console, the norms and the assignment of a project to an organization stay with the platform team.
- **Tenant isolation is by project**: every project route resolves the project through the same visibility filter as before (404 for a project of another organization). Master data live under `<EPC_DATA>/orgs/<slug>/`; the platform team outside any organization keeps the root of `<EPC_DATA>`. Data tied to a project (title block, issuer, team) are always resolved in the data of the **project's** organization, whoever looks at it.
- A new organization starts with itself as its first issuing company; it adds others (an independent professional may issue for several companies) and each project picks one once.
- Personnel carry their functions (designer, checker, approver, responsible, project manager, product owner, inspector, auditor); the team pickers of a project suggest the people with the function.

- The engineering team (and the development MASTER) can **view as** an organization: owner, administrator or member, or the independent professional of an organization of one person. It is a property of the session set by `POST /api/auth/view-as`, allowed only to a stored staff account, which makes the server apply that account type's rights and the organization's visibility; it only ever lowers the team's rights, and each start and end is audited.

## Consequences
- (+) One engine of data, many organizations; the screens only hide what the server already refuses.
- (-) Project folders are still `<client code>/<project code>` in a single namespace: two organizations that use the same client and project codes collide (the second gets "already exists"). Namespacing the folders by organization is the next step.
