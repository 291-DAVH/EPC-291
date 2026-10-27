# epc-plan

Plan-drawing engine: nodes and lines drawn over a plan become a graph with correlative tags, circuit routes (moment-method lengths), schedules and DXF. Profiles: low-voltage electrical and sanitary sewer. Pure functions; depends only on `ezdxf`.
Run: `python -m epc_plan --demo`.

Coordination between disciplines (ADR-0024): `epc_plan.footprint` turns a drawing into what it occupies (metres, heights, free space) and `epc_plan.clash` finds the clashes between footprints of different disciplines with rules that are data (`clash_rules.json`; company and project levels merge with `merge_rules`). `epc_plan.occupancy` says how full a tray or a conduit is. Typical sizes are in each profile (`geom`) and limits in `params.json`; the engineer confirms them for the project.
