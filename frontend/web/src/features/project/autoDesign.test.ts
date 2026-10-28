import { describe, expect, it } from "vitest";
import { applySizing, attention, sizeLabel, Sizing } from "./autoDesign";
import type { Drawing } from "./planEditing";

const drawing = { discipline: "electrica_BT", scale: null, origin: [0, 0], nodes: [], circuits: [], lines: [{ id: "l1", kind: "CN", points: [[0, 0], [1, 0]] }, { id: "l2", kind: "BN", points: [[0, 0], [5, 0]], attrs: { material: "acero" } }, { id: "l3", kind: "CN", points: [[0, 0], [0, 1]] }] } as unknown as Drawing;
const sizing: Sizing = {
  containers: [{ line: "l1", tag: "CN-1", kind: "CN", circuits: ["A"], cables: 1, size: { diametro_mm: 20 }, used_pct: 40, limit_pct: 53, cable_mm: [10.5], fits: true },
               { line: "l2", tag: "BN-1", kind: "BN", circuits: ["A", "B"], cables: 2, size: { ancho_mm: 100, alto_mm: 50 }, used_pct: 12, limit_pct: 50, cable_mm: [10.5, 13.5], fits: true }],
  circuits: [{ tag: "A", section_mm2: 2.5, complies: true, plenums: [], rise_m: 0, found: true }, { tag: "B", section_mm2: null, plenums: ["PL1"], rise_m: 3, found: true }], warnings: [],
};

describe("automatic design: sizing", () => {
  it("writes each size on its line, with the cable diameter the fill was made with, and leaves the other lines and attributes alone", () => {
    const out = applySizing(drawing, sizing);
    expect(out.lines[0].attrs).toEqual({ diametro_mm: 20, diametro_cable_mm: 10.5 });
    expect(out.lines[1].attrs).toEqual({ material: "acero", ancho_mm: 100, alto_mm: 50, diametro_cable_mm: 12 });
    expect(out.lines[2]).toBe(drawing.lines[2]);
  });

  it("labels a conduit by its diameter and a tray by its width and height", () => {
    expect([sizeLabel({ diametro_mm: 25 }), sizeLabel({ ancho_mm: 200, alto_mm: 50 })]).toEqual(["Ø25", "200×50"]);
  });

  it("points at the circuits with no cable and the stretches nothing holds", () => {
    expect(attention(sizing)).toEqual({ circuits: ["B"], containers: [] });
    expect(attention({ ...sizing, containers: [{ ...sizing.containers[0], fits: false }] }).containers).toEqual(["CN-1"]);
  });
});
