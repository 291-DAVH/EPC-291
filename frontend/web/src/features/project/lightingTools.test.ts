import { describe, expect, it } from "vitest";
import { addRoom } from "./planTools";
import { blank, Drawing, setScale } from "./planEditing";
import { applyLighting, hasPlacements, isDrawn, isReady, LightingProposal, marksOf, requestOf, RoomResult, setRoomLighting } from "./lightingApi";
import { applyTemplate, contoursOf, copyLighting, levelsOf, removeTemplate, saveTemplate, setSetting, settingsOf, settingsOptions, suggestActivity } from "./lightingTools";

const room = (d: Drawing, name: string, x: number): Drawing => addRoom(d, name, [[x, 0], [x + 60, 0], [x + 60, 40], [x, 40]]);
const sheet = (): Drawing => room(room(room(setScale(blank(), [0, 0], [100, 0], 10), "Aula", 0), "Pasillo", 100), "Depósito", 200);

describe("what the person sets for the panel of a sheet", () => {
  it("is kept with the sheet, an empty value takes it out and a sheet with none has no key", () => {
    let d = setSetting(sheet(), "power_limit_w_m2", 12);
    d = setSetting(d, "auto_luminaire", true);
    expect(settingsOf(d)).toEqual({ power_limit_w_m2: 12, auto_luminaire: true });
    d = setSetting(setSetting(d, "power_limit_w_m2", NaN), "auto_luminaire", false);
    expect("lighting_settings" in d).toBe(false);
  });

  it("goes to the calculation as options: the numbers and the automatic luminaire, nothing else", () => {
    const d = setSetting(setSetting(setSetting(sheet(), "kwh_price", 0.15), "hours_default", 2000), "auto_luminaire", true);
    expect(settingsOptions(settingsOf(d))).toEqual({ kwh_price: 0.15, hours_default: 2000, auto_luminaire: true });
    expect(requestOf(setSetting(d, "map", true), "en", { map: false }).options).toEqual({ kwh_price: 0.15, hours_default: 2000, auto_luminaire: true, map: false });
    expect(settingsOptions(undefined)).toEqual({});
  });

  it("lets a room with a target and no luminaire be calculated only when the luminaire is chosen automatically", () => {
    expect(isReady({ activity: "a" })).toBe(false);
    expect(isReady({ activity: "a" }, true)).toBe(true);
    expect(isReady({ exterior: true, target_lux: 20 }, true)).toBe(false);                      // an exterior area needs its luminaire too
    expect(isReady(undefined, true)).toBe(false);
  });
});

describe("the request to check the plan as it is drawn", () => {
  it("carries the luminaires of the drawing and nothing else", () => {
    let d = sheet();
    d = { ...d, nodes: [{ id: "n1", kind: "LU", x: 10, y: 10, tag: "LU-001", attrs: { lighting: { power_w: 36 } } }, { id: "n2", kind: "TG", x: 5, y: 5 }] };
    const req = requestOf(d, "es", { use_drawn: true });
    expect(req.sheet.nodes).toEqual([{ id: "n1", kind: "LU", x: 10, y: 10, tag: "LU-001", attrs: { lighting: { power_w: 36 } } }]);
    expect(requestOf(d, "es").sheet).not.toHaveProperty("nodes");
  });

  it("is a proposal with nothing to apply, and draws no marks over what is already there", () => {
    const est = { value: 1, reason: "x", confidence: 1 };
    const result = (drawn: boolean) => ({ id: "r1", name: "Aula", method: "lumen", target: est, factors: { cu: est, maintenance: est }, reflectances: { ceiling: est, walls: est, floor: est },
      layout: { drawn, installed: 2, required: 2, rows_across_width: 0, columns_along_length: 0, spacing_check: { along_length: { checked: false }, across_width: { checked: false } } },
      verification: { average_lux: 1, target_lux: 1, complies: true, margin_pct: 0 }, points: { computed: false }, energy: { installed_power_w: null, power_density_w_m2: null } }) as RoomResult;
    const p = (drawn: boolean): LightingProposal => ({ result: { rooms: [result(drawn)], warnings: [], counts: { rooms: 1, luminaires: 2 } }, placements: { r1: [{ tag: "LU-001", x: 1, y: 1, z_m: 2 }] }, rooms: [], skipped: [], warnings: [], fingerprint: "x" });
    expect(isDrawn(p(true))).toBe(true);
    expect(marksOf(p(true))).toEqual([]);
    expect(isDrawn(p(false))).toBe(false);
    expect(marksOf(p(false))).toHaveLength(1);
  });
});

describe("applying again", () => {
  const proposal = (): LightingProposal => ({
    result: { rooms: [{ id: "r1", name: "Aula", layout: { installed: 2 }, energy: { installed_power_w: 80 } } as unknown as RoomResult], warnings: [], counts: { rooms: 1, luminaires: 2 } },
    placements: { r1: [{ tag: "LU-001", x: 10, y: 10, z_m: 2.6 }, { tag: "LU-002", x: 50, y: 10, z_m: 2.6 }] }, rooms: [{ id: "r1", name: "Aula", length_m: 6, width_m: 4, exact: true, corner: [0, 0], power_factor: 0.8 }], skipped: [], warnings: [], fingerprint: "x",
  });
  const withLuminaires = (): Drawing => ({ ...setRoomLighting(sheet(), "r1", { luminaire: "x" }), nodes: [] });

  it("gives each luminaire its apparent power when the luminaire has a power factor, and only its watts when not", () => {
    const out = applyLighting(withLuminaires(), proposal()).drawing.nodes;
    expect(out[0].attrs).toEqual({ lighting: { source: "calc", room: "r1", luminaire: "x", power_w: 40, power_va: 50, height_m: 2.6 } });
    const none = proposal();
    none.rooms[0].power_factor = null;
    expect((applyLighting(withLuminaires(), none).drawing.nodes[0].attrs!.lighting as Record<string, unknown>).power_va).toBeUndefined();
  });

  it("keeps the circuit of each luminaire it replaces in the one that takes its place", () => {
    const first = applyLighting(withLuminaires(), proposal()).drawing;
    const wired: Drawing = { ...first, nodes: first.nodes.map((n, i) => ({ ...n, circuit: i === 0 ? "IUG-01" : "IUG-02", board: "tb" })) };
    const again = proposal();
    again.placements.r1 = [{ tag: "LU-001", x: 12, y: 10, z_m: 2.6 }, { tag: "LU-002", x: 52, y: 10, z_m: 2.6 }, { tag: "LU-003", x: 30, y: 30, z_m: 2.6 }];
    const out = applyLighting(wired, again).drawing.nodes;
    expect(out.map((n) => [n.x, n.circuit])).toEqual([[12, "IUG-01"], [52, "IUG-02"], [30, "IUG-01"]]);          // the new one takes the circuit of the nearest it replaced
    expect(out[0].board).toBe("tb");
    expect(applyLighting(withLuminaires(), proposal()).drawing.nodes.every((n) => !n.circuit)).toBe(true);        // nothing to keep the first time
  });
});

describe("copying, templates and suggestions", () => {
  it("copies what a room says to the others (not to itself, not to rooms that are not there) and replaces what they said", () => {
    let d = setRoomLighting(sheet(), "r1", { activity: "a", luminaire: "x", height_m: 3 });
    d = setRoomLighting(d, "r2", { activity: "other" });
    const out = copyLighting(d, "r1", ["r1", "r2", "r3", "nope"]);
    expect(out.copied).toBe(2);
    expect(out.drawing.rooms!.map((r) => r.lighting)).toEqual([{ activity: "a", luminaire: "x", height_m: 3 }, { activity: "a", luminaire: "x", height_m: 3 }, { activity: "a", luminaire: "x", height_m: 3 }]);
    expect(copyLighting(sheet(), "r1", ["r2"])).toEqual({ drawing: sheet(), copied: 0 });                          // nothing to copy from a room that says nothing
  });

  it("saves a room as a template under a name, applies it to another room and removes it", () => {
    let d = setRoomLighting(sheet(), "r1", { activity: "a", luminaire: "x" });
    d = saveTemplate(d, " Classroom ", "r1");
    expect(Object.keys(settingsOf(d).templates!)).toEqual(["Classroom"]);
    d = applyTemplate(d, "r2", "Classroom");
    expect(d.rooms![1].lighting).toEqual({ activity: "a", luminaire: "x" });
    expect(applyTemplate(d, "r3", "nope")).toBe(d);
    expect(saveTemplate(d, "  ", "r1")).toBe(d);
    d = removeTemplate(d, "Classroom");
    expect("lighting_settings" in d).toBe(false);
  });

  it("suggests the activity a name points to, only when the engine has it", () => {
    const acts = ["education.classroom", "education.evening_classroom", "circulation.indoor", "room.storage"].map((id) => ({ id }));
    expect(suggestActivity("Aula 3", acts)).toBe("education.classroom");
    expect(suggestActivity("Aula nocturna", acts)).toBe("education.evening_classroom");
    expect(suggestActivity("Pasillo norte", acts)).toBe("circulation.indoor");
    expect(suggestActivity("Depósito", acts)).toBe("room.storage");
    expect(suggestActivity("Cocina", acts)).toBeUndefined();
    expect(suggestActivity("Oficina", acts)).toBeUndefined();                                                     // the engine in this test has no such activity
  });
});

describe("the lines of equal illuminance of a map", () => {
  const map = (values: (number | null)[], nx = 3, ny = 3) => ({ x0: 0, y0: 0, dx: 10, dy: 10, nx, ny, values, min: 100, max: 300 });
  const ramp = map([100, 200, 300, 100, 200, 300, 100, 200, 300]);

  it("crosses a gradient in a straight line at the place the level is reached", () => {
    const lines = contoursOf(ramp, 150);
    expect(lines).toHaveLength(2);
    for (const [a, b] of lines) { expect(a[0]).toBeCloseTo(10, 6); expect(b[0]).toBeCloseTo(10, 6); }             // 150 is half way between the centres at x = 5 and x = 15
    expect(contoursOf(ramp, 50)).toEqual([]);
    expect(contoursOf(ramp, 400)).toEqual([]);
  });

  it("gives no line through a cell outside the outline and one around a peak", () => {
    expect(contoursOf(map([100, 200, 300, 100, null, 300, 100, 200, 300]), 150)).toEqual([]);
    const peak = map([100, 100, 100, 100, 300, 100, 100, 100, 100]);
    expect(contoursOf(peak, 200)).toHaveLength(4);
  });

  it("has round levels between the lowest and the highest, and none for a flat room", () => {
    expect(levelsOf(100, 300)).toEqual([150, 200, 250]);
    expect(levelsOf(312, 478, 5)).toEqual([350, 400, 450]);
    expect(levelsOf(100, 100)).toEqual([]);
  });
});

describe("applying the emergency luminaires", () => {
  const emergency = (): LightingProposal => ({
    result: { rooms: [], emergency: [{ id: "r1", name: "Aula", layout: { installed: 2, columns_along_length: 2, rows_across_width: 1 }, criteria: {} as never, verification: { complies: true }, routes: [], energy: { installed_power_w: 6 } }], warnings: [], counts: { rooms: 0, luminaires: 0 } },
    placements: {}, emergency_placements: { r1: [{ tag: "LE-001", x: 10, y: 10, z_m: 2.6 }, { tag: "LE-002", x: 50, y: 10, z_m: 2.6 }] },
    rooms: [{ id: "r1", name: "Aula", length_m: 6, width_m: 4, exact: true, corner: [0, 0], power_factor: null, emergency_power_factor: 0.6 }], skipped: [], warnings: [], fingerprint: "x",
  });
  const withEmergency = (): Drawing => ({ ...setRoomLighting(sheet(), "r1", { luminaire: "x", emergency_luminaire: "em" }), nodes: [] });

  it("draws them as nodes of their own kind, tagged LE-, with the power they say", () => {
    const out = applyLighting(withEmergency(), emergency());
    expect(out).toMatchObject({ added: 2, removed: 0 });
    expect(out.drawing.nodes.map((n) => [n.kind, n.tag])).toEqual([["LE", "LE-001"], ["LE", "LE-002"]]);
    expect(out.drawing.nodes[0].attrs).toEqual({ lighting: { source: "calc", room: "r1", luminaire: "em", power_w: 3, power_va: 5, height_m: 2.6 } });
  });

  it("replaces only the emergency luminaires of the room when applied again, and keeps the lighting ones and their tags apart", () => {
    const lighting = (): LightingProposal => ({ ...emergency(), result: { rooms: [{ id: "r1", name: "Aula", layout: { installed: 1 }, energy: { installed_power_w: 36 } } as unknown as RoomResult], warnings: [], counts: { rooms: 1, luminaires: 1 } },
                                                  placements: { r1: [{ tag: "LU-001", x: 30, y: 20, z_m: 2.6 }] } });
    const first = applyLighting(withEmergency(), lighting()).drawing;
    expect(first.nodes.map((n) => n.tag)).toEqual(["LU-001", "LE-001", "LE-002"]);
    const again = emergency();
    again.emergency_placements = { r1: [{ tag: "LE-001", x: 30, y: 10, z_m: 2.6 }] };
    const out = applyLighting(first, again);
    expect(out).toMatchObject({ added: 1, removed: 2 });
    expect(out.drawing.nodes.map((n) => n.tag)).toEqual(["LU-001", "LE-001"]);
  });

  it("is something to apply when there are only emergency luminaires", () => {
    expect(hasPlacements(emergency())).toBe(true);
  });
});
