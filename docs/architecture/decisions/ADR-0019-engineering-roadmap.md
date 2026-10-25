# ADR-0019: What the engineering area grows into

Status: Accepted (direction; each item is built when scheduled). Date: 2026-10-25. Extends ADR-0012, ADR-0016.

## Context
Engineering (Ingeniería) already has criteria, boards with their own data, calculation, memo and summary, the real route of every cable, the sheet's issuer and team, and issuing. The next steps were collected and **all accepted**. Starred items (★) are the ones to build first because they use what already exists and are visible at once.

## Decision
**Calculation**
- ★ Short-circuit current chained between boards: the Icc of a downstream board is calculated from the upstream board's and the impedance of its supply cable (with its route), not typed.
- ★ Selectivity with the manufacturer's real curves and selectivity / back-up tables, from an equipment library (miniature and moulded-case breakers, residual-current devices), replacing the normative bands where the data exist.
- Voltage drop during motor starting and choice of the starting method (direct, star-delta, soft starter, drive).
- Demand and simultaneity factors per kind of load; phase balance.
- Reactive-power compensation: present power factor, capacitor bank, effect on the supply.
- Earthing: grounding grid and protective conductor.
- Generator, UPS and emergency loads: sizing and autonomy.
- Lighting: expose the engine's lighting module in the screens.

**Documents that come out of what is already calculated**
- ★ Cable schedule: origin, destination, section, length and route by stretch.
- ★ Load schedule per board in Excel and PDF, with spare capacity and phase balance.
- Bill of quantities and budget from the equipment library; quotation from there.
- Labels for cables and boards, ready to print.
- Descriptive report and specification linked to the project's data, so nothing is written twice.

**Team work and control**
- ★ Revisions (Rev A, B...) with a comparison between them: which circuits changed section, protection or route, and why.
- Approval flow design -> check -> approve, locking the approved board and recording who approved and when.
- Comments and observations per circuit by the reviewer or inspector.
- Traceability requirement -> circuit.
- Reusable board templates across projects.

**Screens**
- ★ Installation tree: grid -> main board -> sub-boards, with status (complies or not), Icc and accumulated voltage drop at every node, and a general single-line diagram that joins the boards.
- Graphic view of each cable's route (see ADR-0020).
- "What if": compare alternatives (copper or aluminium, PVC or XLPE, another section) with cost and compliance side by side.
- Import the load schedule from Excel to start a board without typing.
- Alerts when a change breaks something: "this change makes 3 circuits stop complying".

**Other disciplines** follow the same pattern (data -> calculation -> memo and summary): fire protection and hydraulics (the engine already has Hazen-Williams), HVAC (air flows), and drainage and storm water (ADR-0020).

## Consequences
- (+) A direction the team can pick items from; the starred ones need no new foundations.
- (-) It is a long list: every item still needs its own design, tests and, where the norms matter, validation by the norm reviewer.
