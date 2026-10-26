# ADR-0021: Plan-drawing editor — decisions on the PRD v0.2

Status: Accepted (direction; to be built in phases). Date: 2026-10-26. Refines ADR-0020. Source: `incoming/plan/docs/PRD-trazado-v0.2.md` and its review.

## Decisions
1. **Outputs.** The SVG is the on-screen view only. The deliverables are **DXF and PDF**. DXF output moves to phase 1.
2. **Tags.** A cable "line" references the tag of the circuit in the board (ADR-0012); the editor creates tags only for what does not exist elsewhere (chambers, trays, pipe stretches).
3. **Levels.** Every plan has a level: `L0` is the ground level, `L1`, `L2` … `LN` go up, `L-1`, `L-2` … `L-N` go down.
4. **Permissions.** The drawing belongs to the project and follows the organization's engineering permissions (ADR-0013, ADR-0016); it has no authentication of its own.
5. **Drawing as lines, stored as a graph.** Networks (sewer, gas, fire, ducts) are drawn as lines: a trunk and branches that start or end on it. The program turns them into a graph (nodes and stretches). Rules: a branch connects to the trunk only where its end lies on it (within a snap tolerance), which creates a node and splits the trunk there; two lines that merely cross are **not** connected unless the user places a node; the user marks the outlet of the network (the root) so that flow direction and slopes can be worked out.
6. **Slopes and invert levels.** Not typed per chamber: the program calculates them from the distance and connection between chambers, applying the minimum slope for the diameter from the norm data (reviewed rules, ADR-0011; pending until approved). The user gives the invert level at the outlet.
7. **Containers.** Which cables run in which tray is derived from the routes, as long as both reference each other (the tray stretch and the cable route share the stretch).
8. **Coordinates.** Every plan has an origin `0,0` that the user sets with a button; coordinates are real metres from that origin, after the two-point scale calibration.
9. **DXF.** Generated from the model with `ezdxf`, never converted from the SVG. The user can choose the DXF version; the default is the latest `ezdxf` writes (R2018). The gate runs `ezdxf` audit; opening in AutoCAD is a manual check by the owner, recorded as not verified locally.

10. **Circuits over the drawing (owner, 2026-10-26).** A circuit is not drawn cable by cable: the person chooses a circuit of the board (a reference), its origin node, its destination node and its number of parallel cables (ternas), and the program routes it by the shortest way over the drawn stretches. A **conduit (and a road crossing) takes a single circuit**: once a circuit uses it, it is blocked for the others (its ternas may share it); a **tray takes several circuits and several ternas**. Each stretch records what it carries and how many cables; a circuit with no free way is reported, not forced.

11. **Loads (owner, 2026-10-26).** Luminaires (LU), general-use sockets (TG, TUG), special-use sockets (TE, TUE) and HVAC units (HV) are nodes that can be placed on the plan and given a circuit of the board. They can be selected together (a box, Shift-click, or all of one kind) and assigned to a circuit at once. A circuit with loads is routed from its origin node to every one of them (the shared trunk counted once, the distance to each load reported); loads without a circuit are listed with a warning.

## Consequences
- (+) One model feeds the schedules, the DXF and the PDF; the cable data stays in one place.
- (-) The line-to-graph conversion needs clear rules for junctions and crossings and a visible way to correct them.
- (-) Slopes depend on the norm data being reviewed and approved before they can be called validated.

## Still open
Library for the canvas (SVG with zoom or canvas under MIT); which disciplines follow electrical LV (proposal: fire protection and sewer).
