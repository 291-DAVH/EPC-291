# ADR-0008: CAD strategy: 2D first with ezdxf and shapely

Status: Accepted. Date: 2026-10-23.

## Context
The product produces diagrams and drawings (single-line and multi-line diagrams, layouts, title blocks) delivered as DXF. The engine is mathematics-heavy and written in Python. A full CAD environment, and later 3D through FreeCAD, were considered, as was a Rust desktop edition (ADR-0007).

## Decision
- All drawing work is **2D**, in Python: **ezdxf** reads and writes DXF (layers, blocks, attributes, dimensions) and **shapely** provides geometry (polygons, offsets, unions, intersections, clearances, nesting in sheets). Both are already dependencies of `engine/drawing`.
- Drawing code stays in `engine/drawing`; when it grows beyond diagrams, a common `engine/cad` interface (entities, layers, blocks, queries) is extracted so the rest of the system does not depend on a library directly.
- **FreeCAD, 3D and BIM are out of scope for now.** If revisited, FreeCAD would run as a separate process behind the same interface, and the license (LGPL) would be reviewed before packaging.
- **Rust is out of scope for now**, including the desktop edition (ADR-0007 is deferred). The engine stays Python.

## Consequences
- (+) One small, well-known stack; DXF is the deliverable format already, so no conversion layer.
- (+) Nothing to package besides Python dependencies.
- (-) No 3D, no parametric solids, no BIM exchange (IFC) until the decision is revisited.
- (-) An interactive CAD editor in the web app would have to be built on a canvas over our own geometry model; it is not planned.
