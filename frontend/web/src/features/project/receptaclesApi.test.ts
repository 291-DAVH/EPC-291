import { describe, expect, it } from "vitest";
import { addRoom } from "./planTools";
import { blank, Drawing, setScale } from "./planEditing";
import { applyReceptacles, CALC, hasPlacements, isDrawn, isReady, marksOf, ReceptaclesProposal, requestOf, setRoomReceptacles } from "./receptaclesApi";

const room = (d: Drawing, name: string): Drawing => addRoom(d, name, [[0, 0], [60, 0], [60, 40], [0, 40]]);
const twoRooms = (): Drawing => room(room(setScale(blank(), [0, 0], [100, 0], 10), "Oficina"), "Pasillo");

const proposal = (over: Partial<ReceptaclesProposal> = {}): ReceptaclesProposal => ({
  result: { rooms: [{ id: "r1", name: "Oficina", use: "office", basis: "area", family: "TUG", receptacle: "tug_2x10_t", area_m2: 24, perimeter_m: 20, required: 2, installed: 2, power_va_each: 100, load_va: 200, circuits_min: 1,
            layout: { mode: "proposed" }, checks: [], estimate: { reason: "x", confidence: 0.4, source: "typical" } }], warnings: [], counts: { rooms: 1, outlets: 2, required: 2, warnings: 0 } },
  placements: { r1: [{ tag: "R1", x: 10, y: 0, z_m: 0.3, wall: "south", kind: "TG" }, { tag: "R2", x: 60, y: 20, z_m: 0.3, wall: "east", kind: "TG" }] },
  skipped: [], warnings: [], ...over,
});

describe("what a room says about its outlets", () => {
  it("is saved with the room, merged with what it already said, and an empty value takes the key out", () => {
    let d = setRoomReceptacles(twoRooms(), "r1", { use: "office", receptacle: "tug_2x10_t" });
    d = setRoomReceptacles(d, "r1", { count: 5, receptacle: "" });
    expect(d.rooms![0].receptacles).toEqual({ use: "office", count: 5 });
    expect(d.rooms![1].receptacles).toBeUndefined();
  });

  it("leaves a room without `receptacles` when nothing is left and a room is ready when it says its use", () => {
    let d = setRoomReceptacles(twoRooms(), "r1", { use: "office" });
    expect(isReady(d.rooms![0].receptacles)).toBe(true);
    d = setRoomReceptacles(d, "r1", { use: undefined, height_m: NaN });
    expect("receptacles" in d.rooms![0]).toBe(false);
    expect(isReady(d.rooms![0].receptacles)).toBe(false);
  });
});

describe("the request of the calculation", () => {
  it("carries the outlines and only the rooms that say something", () => {
    const d = setRoomReceptacles(twoRooms(), "r1", { use: "office", count: 3 });
    const r = requestOf(d, "es");
    expect(Object.keys(r.rooms)).toEqual(["r1"]);
    expect(r.rooms.r1).toEqual({ use: "office", count: 3 });
    expect(r.sheet.rooms).toHaveLength(2);
    expect(r.sheet.nodes).toBeUndefined();
  });

  it("sends the outlets drawn, and only those, when the plan is checked as it is", () => {
    let d = setRoomReceptacles(twoRooms(), "r1", { use: "office" });
    d = { ...d, nodes: [{ id: "a", kind: "TG", x: 5, y: 5 }, { id: "b", kind: "LU", x: 6, y: 6 }, { id: "c", kind: "TE", x: 7, y: 7 }] };
    expect(requestOf(d, "en", { use_drawn: true }).sheet.nodes!.map((n) => n.id)).toEqual(["a", "c"]);
  });
});

describe("the proposal over the plan", () => {
  it("shows its outlets as marks until it is applied, and a check of what is drawn has nothing to apply", () => {
    expect(marksOf(proposal()).map((m) => m.tag)).toEqual(["R1", "R2"]);
    expect(hasPlacements(proposal())).toBe(true);
    const drawn = proposal({ result: { ...proposal().result!, rooms: [{ ...proposal().result!.rooms[0], layout: { mode: "drawn" } }] } });
    expect(isDrawn(drawn)).toBe(true);
    expect([marksOf(drawn).length, hasPlacements(drawn)]).toEqual([0, false]);
    expect(marksOf(null)).toEqual([]);
  });

  it("puts the outlets in the drawing with their room, their outlet and their power, numbered by kind", () => {
    const out = applyReceptacles(twoRooms(), proposal());
    expect([out.added, out.removed]).toEqual([2, 0]);
    expect(out.drawing.nodes.map((n) => n.tag)).toEqual(["TG-001", "TG-002"]);
    expect(out.drawing.nodes[0].attrs).toEqual({ receptacles: { source: CALC, room: "r1", receptacle: "tug_2x10_t", power_va: 100, height_m: 0.3 } });
  });

  it("replaces the outlets of an earlier calculation, keeps the circuit of the nearest and does not touch what was drawn by hand", () => {
    const first = applyReceptacles(twoRooms(), proposal()).drawing;
    const wired = { ...first, nodes: first.nodes.map((n, i) => (i === 0 ? { ...n, circuit: "TUG-01", board: "b1" } : n)).concat([{ id: "hand", kind: "TG", x: 1, y: 1, tag: "TG-099" }]) };
    const again = applyReceptacles(wired, proposal({ placements: { r1: [{ tag: "R1", x: 12, y: 0, z_m: 0.3, wall: "south", kind: "TG" }] } }));
    expect([again.added, again.removed]).toEqual([1, 2]);
    const fresh = again.drawing.nodes.find((n) => n.x === 12)!;
    expect([fresh.circuit, fresh.board]).toEqual(["TUG-01", "b1"]);                  // the nearest old one had it
    expect(again.drawing.nodes.some((n) => n.id === "hand")).toBe(true);
    expect(fresh.tag).toBe("TG-100");                                                // goes on from the highest of the drawing
  });

  it("places a special-use outlet as a TE node with its own numbering", () => {
    const p = proposal({ placements: { r1: [{ tag: "R1", x: 10, y: 0, z_m: 1.2, wall: "south", kind: "TE" }] } });
    expect(applyReceptacles(twoRooms(), p).drawing.nodes.map((n) => [n.kind, n.tag])).toEqual([["TE", "TE-001"]]);
  });
});
