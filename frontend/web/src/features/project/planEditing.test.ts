import { describe, expect, it } from "vitest";
import { addCircuit, addLine, addNode, assignCircuit, blank, moveElements, moveSegment, stretchEnd, inBox, loadsOf, merge, ofKind, removeMany, toggle, freeCircuits, parseAttr, removeCircuit, setAttr, updateCircuit, updateLine, commit, levelNumber, metresPerUnit, nextId, nextLevel, ortho, pick, redo, remove, setOrigin, setScale, snap, undo } from "./planEditing";

describe("plan editing rules", () => {
  it("gives ids that are unique across nodes and lines", () => {
    let d = addNode(blank(), "CM", [0, 0]);
    d = addNode(d, "CM", [10, 0]);
    d = addLine(d, "BN", [[0, 0], [10, 0]]);
    expect(d.nodes.map((n) => n.id)).toEqual(["n1", "n2"]);
    expect(d.lines.map((l) => l.id)).toEqual(["l1"]);
    expect(nextId(d, "n")).toBe("n3");
  });

  it("does not add a line with fewer than two points", () => {
    const d = blank();
    expect(addLine(d, "BN", [[0, 0]])).toBe(d);
  });

  it("removes a node and forgets it as the outlet; removes a line", () => {
    let d = { ...addNode(blank(), "BR", [0, 0]), outlet: "n1" };
    d = addLine(d, "CC", [[0, 0], [5, 5]]);
    expect(remove(d, { type: "node", id: "n1" }).outlet).toBe("");
    expect(remove(d, { type: "line", id: "l1" }).lines).toEqual([]);
  });

  it("calibrates the scale from two points and a real distance, and refuses nonsense", () => {
    const d = setScale(blank(), [0, 0], [30, 40], 5);
    expect(metresPerUnit(d)).toBeCloseTo(0.1);
    expect(setScale(blank(), [1, 1], [1, 1], 5).scale).toBeNull();
    expect(setScale(blank(), [0, 0], [1, 0], 0).scale).toBeNull();
    expect(metresPerUnit(blank())).toBeNull();
  });

  it("sets the origin", () => {
    expect(setOrigin(blank(), [12, 34]).origin).toEqual([12, 34]);
  });

  it("snaps a click to a nearby node or line end, otherwise keeps it", () => {
    const d = addLine(addNode(blank(), "CM", [100, 100]), "BN", [[0, 0], [50, 0]]);
    expect(snap(d, [103, 98], 8)).toEqual([100, 100]);
    expect(snap(d, [52, 3], 8)).toEqual([50, 0]);
    expect(snap(d, [70, 70], 8)).toEqual([70, 70]);
  });

  it("keeps a segment horizontal or vertical with ortho", () => {
    expect(ortho([0, 0], [10, 3])).toEqual([10, 0]);
    expect(ortho([0, 0], [2, 9])).toEqual([0, 9]);
  });

  it("picks the node over the line under it, then the line, then nothing", () => {
    const d = addLine(addNode(blank(), "CM", [10, 0]), "BN", [[0, 0], [20, 0]]);
    expect(pick(d, [11, 1], 4)).toEqual({ type: "node", id: "n1" });
    expect(pick(d, [3, 2], 4)).toEqual({ type: "line", id: "l1" });
    expect(pick(d, [3, 30], 4)).toBeNull();
  });

  it("names levels from L0 up and down", () => {
    expect(nextLevel([], "up")).toBe("L0");
    expect(nextLevel(["L0"], "up")).toBe("L1");
    expect(nextLevel(["L-1", "L0", "L2"], "up")).toBe("L3");
    expect(nextLevel(["L-1", "L0", "L2"], "down")).toBe("L-2");
    expect(levelNumber("L-3")).toBe(-3);
  });

  it("undoes and redoes whole drawings", () => {
    const a = blank();
    const b = addNode(a, "CM", [1, 1]);
    let h = commit({ past: [], future: [] }, a);
    const u = undo(h, b);
    expect(u.d).toBe(a);
    h = u.h;
    expect(redo(h, u.d).d).toBe(b);
    expect(undo({ past: [], future: [] }, b).d).toBe(b);
  });

  it("turns typed attribute values into numbers when they look like numbers", () => {
    expect(parseAttr(" 2,5 ")).toBe(2.5);
    expect(parseAttr("-3")).toBe(-3);
    expect(parseAttr("PVC")).toBe("PVC");
    expect(parseAttr("  ")).toBeUndefined();
    expect(setAttr({ a: 1, b: 2 }, "a", "")).toEqual({ b: 2 });
    expect(setAttr(undefined, "ancho_mm", "300")).toEqual({ ancho_mm: 300 });
  });

  it("edits a line without touching the others", () => {
    const d = addLine(addLine(blank(), "BN", [[0, 0], [1, 0]]), "CN", [[0, 0], [0, 1]]);
    const e = updateLine(d, "l1", { tag: "BN-9" });
    expect(e.lines[0].tag).toBe("BN-9");
    expect(e.lines[1]).toBe(d.lines[1]);
  });

  it("adds, edits and removes routed circuits, and offers the board circuits not yet routed", () => {
    let d = addCircuit(blank(), "C-01");
    d = updateCircuit(d, 0, { from: "n1", to: "n2", ternas: 2 });
    expect(d.circuits).toEqual([{ tag: "C-01", from: "n1", to: "n2", ternas: 2 }]);
    expect(freeCircuits(d, ["C-01", "C-02"])).toEqual(["C-02"]);
    expect(removeCircuit(d, 0).circuits).toEqual([]);
  });

  it("selects by box, by kind, and toggles or merges selections", () => {
    let d = addNode(addNode(addNode(blank(), "LU", [10, 10]), "LU", [200, 200]), "TG", [20, 20]);
    d = addLine(d, "BN", [[5, 5], [30, 5]]);
    expect(inBox(d, [0, 0], [40, 40])).toEqual([{ type: "node", id: "n1" }, { type: "node", id: "n3" }, { type: "line", id: "l1" }]);
    expect(inBox(d, [40, 40], [0, 0]).length).toBe(3);
    expect(ofKind(d, "LU")).toEqual([{ type: "node", id: "n1" }, { type: "node", id: "n2" }]);
    expect(toggle([{ type: "node", id: "n1" }], { type: "node", id: "n1" })).toEqual([]);
    expect(merge([{ type: "node", id: "n1" }], [{ type: "node", id: "n1" }, { type: "node", id: "n2" }]).length).toBe(2);
    expect(removeMany(d, [{ type: "node", id: "n1" }, { type: "line", id: "l1" }]).nodes.length).toBe(2);
  });

  it("assigns the selected loads to a circuit and ignores what is not a load", () => {
    const loads = new Set(["LU", "TG"]);
    let d = addNode(addNode(addNode(blank(), "LU", [0, 0]), "TG", [1, 1]), "CM", [2, 2]);
    const all = d.nodes.map((n) => ({ type: "node" as const, id: n.id }));
    const r = assignCircuit(d, all, "C-05", loads);
    expect(r.changed).toBe(2);
    expect(r.drawing.nodes.map((n) => n.circuit)).toEqual(["C-05", "C-05", undefined]);
    expect(loadsOf(r.drawing, "C-05", loads)).toBe(2);
    const cleared = assignCircuit(r.drawing, all, "", loads);
    expect(cleared.drawing.nodes.every((n) => n.circuit === undefined)).toBe(true);
    d = r.drawing;
    expect(d.nodes[2].circuit).toBeUndefined();
  });

  it("moves nodes and lines; lines ending on a moved node follow it", () => {
    let d = addNode(addNode(blank(), "LU", [0, 0]), "LU", [50, 0]);
    d = addLine(d, "BN", [[0, 0], [50, 0]]);
    const a = moveElements(d, [{ type: "node", id: "n1" }], 10, 5);
    expect(a.nodes[0]).toMatchObject({ x: 10, y: 5 });
    expect(a.lines[0].points).toEqual([[10, 5], [50, 0]]);
    const b = moveElements(d, [{ type: "line", id: "l1" }], 3, 4);
    expect(b.lines[0].points).toEqual([[3, 4], [53, 4]]);
    expect(b.nodes[0]).toMatchObject({ x: 0, y: 0 });
    expect(moveElements(d, [{ type: "node", id: "n1" }], 0, 0)).toBe(d);
  });

  it("stretches a line end along its axis and moves a segment sideways keeping the joined nodes", () => {
    let d = addNode(blank(), "LU", [100, 0]);
    d = addLine(d, "BN", [[0, 0], [100, 0], [100, 50]]);
    const a = stretchEnd(d, "l1", 1, [100, 80]);
    expect(a.lines[0].points[2]).toEqual([100, 80]);
    expect(stretchEnd(d, "l1", 1, [300, 20]).lines[0].points[2]).toEqual([100, 20]);
    expect(stretchEnd(d, "l1", 1, [100, -9])).toBe(d);
    const b = moveSegment(d, "l1", 1, [40, 7]);
    expect(b.lines[0].points).toEqual([[0, 0], [140, 0], [140, 50]]);
    expect(b.nodes[0]).toMatchObject({ x: 140, y: 0 });
    const c = moveSegment(d, "l1", 0, [5, 30]);
    expect(c.lines[0].points[0]).toEqual([0, 30]);
    expect(c.lines[0].points[1]).toEqual([100, 30]);
  });
});
