import { describe, expect, it } from "vitest";
import { addRoom } from "./planTools";
import { blank, Drawing, setScale } from "./planEditing";
import { applyLighting, cardOf, hasPlacements, isReady, LightingProposal, marksOf, parsePositive, requestOf, RoomResult, setRoomLighting } from "./lightingApi";

const square = (d: Drawing, name: string): Drawing => addRoom(d, name, [[0, 0], [60, 0], [60, 40], [0, 40]]);
const twoRooms = (): Drawing => square(square(setScale(blank(), [0, 0], [100, 0], 10), "Aula"), "Pasillo");

const estimate = (value: number, confidence: number) => ({ value, reason: "x", confidence });
const result = (over: Partial<RoomResult> = {}): RoomResult => ({
  id: "r1", name: "Aula", method: "lumen",
  target: estimate(300, 0.9), factors: { cu: estimate(0.97, 1), maintenance: estimate(0.8, 0.8) }, reflectances: { ceiling: estimate(0.575, 0.7), walls: estimate(0.775, 0.7), floor: estimate(0.15, 0.7) },
  layout: { installed: 2, required: 2, rows_across_width: 1, columns_along_length: 2, spacing_check: { along_length: { checked: true, status: "within_tolerance" }, across_width: { checked: false } } },
  verification: { average_lux: 310.4, target_lux: 300, complies: true, margin_pct: 3.467 },
  points: { computed: true, min_over_avg: 0.139 }, energy: { installed_power_w: 128, power_density_w_m2: 5.33 },
  ...over,
});

describe("what a room says about its lighting", () => {
  it("is saved with the room, merged with what it already said, and an empty value takes the key out", () => {
    let d = setRoomLighting(twoRooms(), "r1", { activity: "education.classroom", luminaire: "led_panel_600" });
    d = setRoomLighting(d, "r1", { height_m: 2.8, activity: "" });
    expect(d.rooms![0].lighting).toEqual({ luminaire: "led_panel_600", height_m: 2.8 });
    expect(d.rooms![1].lighting).toBeUndefined();                                         // the other room is not touched
  });

  it("leaves a room without `lighting` when nothing is left, and ignores a value that is not a number", () => {
    let d = setRoomLighting(twoRooms(), "r1", { luminaire: "x" });
    d = setRoomLighting(d, "r1", { luminaire: undefined, target_lux: NaN });
    expect("lighting" in d.rooms![0]).toBe(false);
  });

  it("is ready to calculate with a luminaire and an activity or a target", () => {
    expect(isReady(undefined)).toBe(false);
    expect(isReady({ luminaire: "x" })).toBe(false);
    expect(isReady({ luminaire: "x", activity: "a" })).toBe(true);
    expect(isReady({ luminaire: "x", target_lux: 300 })).toBe(true);
    expect(isReady({ activity: "a" })).toBe(false);
  });

  it("reads a number typed with a comma and refuses what is not a positive number", () => {
    expect(parsePositive("2,6")).toBe(2.6);
    expect(parsePositive(" 300 ")).toBe(300);
    for (const bad of ["", "0", "-1", "abc", "Infinity"]) expect(parsePositive(bad)).toBeUndefined();
  });
});

describe("the request of the calculation", () => {
  it("carries the scale, every outline and only what the rooms that said something said", () => {
    let d = setRoomLighting(twoRooms(), "r1", { activity: "education.classroom", luminaire: "led_panel_600", method: "zonal", height_m: 2.8 });
    d = { ...d, rooms: d.rooms!.map((r) => (r.id === "r1" ? { ...r, lighting: { ...r.lighting, junk: 1 } as never } : r)) };
    const req = requestOf(d, "es", { compute_points: false });
    expect(req.sheet.scale).toEqual(d.scale);
    expect(req.sheet.rooms.map((r) => r.id)).toEqual(["r1", "r2"]);
    expect(Object.keys(req.rooms)).toEqual(["r1"]);
    expect(req.rooms.r1).toEqual({ activity: "education.classroom", luminaire: "led_panel_600", method: "zonal", height_m: 2.8 });      // nothing outside what the backend knows
    expect(req.lang).toBe("es");
    expect(req.options).toEqual({ compute_points: false });
  });
});

describe("what the panel shows of a result", () => {
  it("summarises a room: the verdict against the target, the spacing, the uniformity and the power", () => {
    const c = cardOf(result());
    expect(c).toMatchObject({ installed: 2, required: 2, average: 310.4, target: 300, complies: true, spacing: "tolerance", uniformity: 0.139, power_w: 128 });
    expect(c.unsure).toEqual([]);                                                          // everything estimated was sure enough
  });

  it("flags what was estimated with little confidence, and says nothing of the uniformity when the points were not computed", () => {
    const c = cardOf(result({ factors: { cu: estimate(0.9, 0.4), maintenance: estimate(0.8, 0.8) }, points: { computed: false, min_over_avg: 0.2 } }));
    expect(c.unsure).toEqual(["cu"]);
    expect(c.uniformity).toBeNull();
  });

  it("reads the spacing of each axis: the worst one counts and an axis not checked does not", () => {
    const axis = (status: "ok" | "within_tolerance" | "exceeds") => ({ checked: true, status });
    const spacing = (a: ReturnType<typeof axis> | { checked: false }, b: ReturnType<typeof axis> | { checked: false }) => cardOf(result({ layout: { ...result().layout, spacing_check: { along_length: a, across_width: b } } })).spacing;
    expect(spacing(axis("ok"), axis("exceeds"))).toBe("over");
    expect(spacing(axis("ok"), axis("within_tolerance"))).toBe("tolerance");
    expect(spacing(axis("ok"), { checked: false })).toBe("ok");
    expect(spacing({ checked: false }, { checked: false })).toBe("na");
  });
});

describe("the luminaires over the plan", () => {
  const proposal: LightingProposal = {
    result: null, rooms: [], skipped: [], warnings: [], fingerprint: "x",
    placements: { r1: [{ tag: "LU-001", x: 15, y: 20, z_m: 2.6 }, { tag: "LU-002", x: 45, y: 20, z_m: 2.6 }], r2: [{ tag: "LU-003", x: 5, y: 60, z_m: 2.6 }] },
  };

  it("become one mark per luminaire, with the room it belongs to", () => {
    expect(marksOf(proposal).map((m) => [m.room, m.tag, m.at])).toEqual([["r1", "LU-001", [15, 20]], ["r1", "LU-002", [45, 20]], ["r2", "LU-003", [5, 60]]]);
  });

  it("are nothing when there is no proposal", () => {
    expect(marksOf(null)).toEqual([]);
  });
});

describe("applying the luminaires to the plan", () => {
  const room = (id: string): RoomResult => result({ id, layout: { ...result().layout, installed: 2 }, energy: { installed_power_w: 80, power_density_w_m2: 3 } });
  const proposal = (over: Partial<LightingProposal> = {}): LightingProposal => ({
    result: { rooms: [room("r1")], warnings: [], counts: { rooms: 1, luminaires: 2 } }, rooms: [], skipped: [], warnings: [], fingerprint: "x",
    placements: { r1: [{ tag: "LU-001", x: 15, y: 20, z_m: 2.6 }, { tag: "LU-002", x: 45, y: 20, z_m: 2.6 }] }, ...over,
  });
  const base = (): Drawing => setRoomLighting(twoRooms(), "r1", { activity: "a", luminaire: "led_panel_600" });

  it("draws one luminaire per placement with its room, its luminaire and its power, and is nothing without placements", () => {
    const out = applyLighting(base(), proposal());
    expect(out).toMatchObject({ added: 2, removed: 0 });
    expect(out.drawing.nodes.map((n) => [n.kind, n.tag, n.x, n.y])).toEqual([["LU", "LU-001", 15, 20], ["LU", "LU-002", 45, 20]]);
    expect(out.drawing.nodes[0].attrs).toEqual({ lighting: { source: "calc", room: "r1", luminaire: "led_panel_600", power_w: 40, height_m: 2.6 } });
    expect(hasPlacements(proposal())).toBe(true);
    expect(hasPlacements(proposal({ placements: { r1: [] } }))).toBe(false);
    expect(applyLighting(base(), proposal({ placements: { r1: [] } }))).toMatchObject({ added: 0, removed: 0 });
  });

  it("replaces what a calculation placed in the room and leaves what the person drew, going on with the tags", () => {
    let d = applyLighting(base(), proposal()).drawing;
    d = { ...d, nodes: [...d.nodes, { id: "own", kind: "LU", x: 1, y: 1, tag: "LU-007" }, { id: "t", kind: "TG", x: 2, y: 2 }] };
    const out = applyLighting(d, proposal({ placements: { r1: [{ tag: "LU-001", x: 30, y: 20, z_m: 2.6 }] } }));
    expect(out).toMatchObject({ added: 1, removed: 2 });
    expect(out.drawing.nodes.map((n) => n.tag ?? n.kind)).toEqual(["LU-007", "TG", "LU-008"]);
  });

  it("does not touch the luminaires a calculation placed in another room", () => {
    const first = applyLighting(base(), proposal()).drawing;
    const out = applyLighting(first, proposal({ result: { rooms: [room("r2")], warnings: [], counts: { rooms: 1, luminaires: 1 } }, placements: { r2: [{ tag: "LU-001", x: 5, y: 60, z_m: 2.6 }] } }));
    expect(out).toMatchObject({ added: 1, removed: 0 });
    expect(out.drawing.nodes).toHaveLength(3);
  });
});
