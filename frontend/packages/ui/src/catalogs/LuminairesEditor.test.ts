import { describe, expect, it } from "vitest";
import { changesOf, Luminaire, visibleIds } from "./LuminairesEditor";

const lum = (over: Partial<Luminaire> = {}): Luminaire => ({ name: { es: "Panel", en: "Panel" }, kind: "interior", lamps: 1, lamp_flux_lm: 3000, power_w: 36, illustrative: true, ...over });

describe("what a level changes in the catalogue of luminaires", () => {
  it("is nothing when the draft is what the level has", () => {
    expect(changesOf({ a: lum() }, { a: lum() })).toEqual({});
  });

  it("is the entries that were edited or added, whole", () => {
    expect(changesOf({ a: lum() }, { a: lum({ power_w: 40 }), b: lum({ lamps: 2 }) })).toEqual({ a: lum({ power_w: 40 }), b: lum({ lamps: 2 }) });
  });

  it("marks as disabled the ones that were taken out", () => {
    expect(changesOf({ a: lum(), b: lum() }, { a: lum() })).toEqual({ b: { disabled: true } });
  });
});

describe("which luminaires the list shows", () => {
  const set = { b: lum({ name: { es: "Regleta", en: "Batten" } }), a: lum({ name: { es: "Panel", en: "Panel" }, group: "Offices", favorite: true }), c: lum({ name: { es: "Campana", en: "High-bay" }, group: "Industry" }) };

  it("lists the favourites first and then by id", () => {
    expect(visibleIds(set, "", "")).toEqual(["a", "b", "c"]);
    expect(visibleIds({ ...set, c: { ...set.c, favorite: true } }, "", "")).toEqual(["a", "c", "b"]);
  });

  it("filters by what was typed in the id or either name, and by group", () => {
    expect(visibleIds(set, "batten", "")).toEqual(["b"]);
    expect(visibleIds(set, " CAMP ", "")).toEqual(["c"]);
    expect(visibleIds(set, "", "Offices")).toEqual(["a"]);
    expect(visibleIds(set, "a", "Industry")).toEqual(["c"]);
    expect(visibleIds(set, "zzz", "")).toEqual([]);
  });
});
