import { describe, expect, it } from "vitest";
import { covers, levelChoices, levelNumber, levelsToMake, otherShafts, PlenumDef, plenumNear, plenumNeededAt, reachOf } from "./plenumFlow";

const plenum = (over: Partial<PlenumDef> = {}): PlenumDef => ({ code: "PL-1", discipline: "electrica_BT", level: "L-1", x_m: 1, y_m: 1, altura_m: 3, up: null, down: null, ...over });

describe("the levels of the building", () => {
  it("reads a level as a number, a sheet key too, and says when it is not one", () => {
    expect([levelNumber("L-1"), levelNumber("L0"), levelNumber("L12"), levelNumber("L-1@electrica_BT")]).toEqual([-1, 0, 12, -1]);
    expect(levelNumber("PB")).toBeNaN();
  });

  it("makes the ground level first when nothing exists, then the ones down to the board, with no gap", () => {
    expect(levelsToMake([], "L0")).toEqual(["L0"]);
    expect(levelsToMake([], "L-1")).toEqual(["L0", "L-1"]);
    expect(levelsToMake([], "L2")).toEqual(["L0", "L1", "L2"]);
    expect(levelsToMake(["L0"], "L-2")).toEqual(["L-1", "L-2"]);
    expect(levelsToMake(["L0", "L1"], "L3")).toEqual(["L2", "L3"]);
  });

  it("makes nothing for a level that exists or lies between the ones that do, or is not a level", () => {
    expect(levelsToMake(["L-1", "L0", "L1"], "L0")).toEqual([]);
    expect(levelsToMake(["L0"], "PB")).toEqual([]);
  });

  it("offers the levels there are and one more on each side, or from three below to three above when none was made", () => {
    expect(levelChoices([])).toEqual(["L-3", "L-2", "L-1", "L0", "L1", "L2", "L3"]);
    expect(levelChoices(["L0", "L1"])).toEqual(["L-1", "L0", "L1", "L2"]);
  });
});

describe("how far a plenum reaches", () => {
  it("crosses its own level and the ones within its reach up and down, or all of them", () => {
    const p = { level: "L0", up: 2, down: 1 };
    expect([-2, -1, 0, 1, 2, 3].map((n) => covers(p, `L${n}`))).toEqual([false, true, true, true, true, false]);
    expect([-5, 0, 7].every((n) => covers({ level: "L-1", up: null, down: null }, `L${n}`))).toBe(true);
  });

  it("reads what the person says: all, or two whole numbers from 0 to 50; anything else is nothing", () => {
    expect(reachOf(true, "", "")).toEqual({ up: null, down: null });
    expect(reachOf(false, "2", "0")).toEqual({ up: 2, down: 0 });
    for (const [u, d] of [["-1", "0"], ["1.5", "0"], ["51", "0"], ["", "1"], ["a", "1"]]) expect(reachOf(false, u, d)).toBeNull();
  });
});

describe("when the plenum is asked for", () => {
  const boards = [{ id: "b", name: "TGBT", level: "L-1" }];

  it("is asked at the level of the board when no plenum crosses it", () => {
    expect(plenumNeededAt(boards, [])).toBe("L-1");
    expect(plenumNeededAt(boards, [plenum({ level: "L0", up: 0, down: 0 })])).toBe("L-1");              // a plenum that does not reach the level of the board is not one for it
  });

  it("is not asked when one crosses the level of the board, or there is no board with a level", () => {
    expect(plenumNeededAt(boards, [plenum()])).toBeNull();
    expect(plenumNeededAt(boards, [plenum({ level: "L0", up: 0, down: 1 })])).toBeNull();               // from the level above, one level down reaches the board
    expect(plenumNeededAt([{ id: "b", name: "TGBT" }], [])).toBeNull();
    expect(plenumNeededAt([], [])).toBeNull();
  });

  it("only counts the plenums of the discipline asked", () => {
    expect(plenumNeededAt(boards, [plenum({ discipline: "sanitaria_cloacas" })])).toBe("L-1");
  });

  it("is proposed a metre to the right of the board, or at the origin when the board is not drawn", () => {
    expect(plenumNear([4.256, 2])).toEqual([5.26, 2]);
    expect(plenumNear(null)).toEqual([0, 0]);
  });

  it("is asked of the other disciplines that have a shaft and a drawing and no plenum yet", () => {
    const profiles = [{ id: "electrica_BT", nodes: [{ id: "PL", vertical: true }] }, { id: "fire", nodes: [{ id: "SH", vertical: true }] }, { id: "civil", nodes: [{ id: "WL" }] }, { id: "hvac", nodes: [{ id: "DU", vertical: true }] }];
    expect(otherShafts(profiles, ["electrica_BT", "fire", "civil"], [], "L0")).toEqual(["fire"]);          // civil has no shaft, hvac has no drawing, electrical is asked on its own
    expect(otherShafts(profiles, ["fire"], [plenum({ discipline: "fire", level: "L0" })], "L0")).toEqual([]);
  });
});
