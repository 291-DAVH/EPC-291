import { describe, expect, it } from "vitest";
import { addLine, addNode, blank, Drawing, setScale } from "./planEditing";
import {
  alignDelta, alignNodes, arrayClip, boundsOf, copyElements, distributeNodes, findProblems, fromMetres, generationChecks, isLocked, measureAngle, normalizeClip, pasteClip,
  polygonArea, selectionStats, setLocked, shortestRoute, snapEx, splitLineAt, spreadLabels, toMetres, transformGroup, unlocked, warningTargets,
} from "./planTools";

const node = (id: string) => ({ type: "node" as const, id });
const line = (id: string) => ({ type: "line" as const, id });

describe("snapping", () => {
  const d = addLine(addNode(blank(), "CM", [100, 100]), "BN", [[0, 0], [50, 0]]);
  it("prefers a node, then a line end, then a reference point, then a midpoint", () => {
    expect(snapEx(d, [103, 98], 8)).toEqual({ p: [100, 100], kind: "node" });
    expect(snapEx(d, [52, 3], 8)).toEqual({ p: [50, 0], kind: "end" });
    expect(snapEx(d, [22, 40], 8, { ref: [[20, 40]] })).toEqual({ p: [20, 40], kind: "ref" });
    expect(snapEx(d, [26, 2], 8, { mid: true })).toEqual({ p: [25, 0], kind: "mid" });
    expect(snapEx(d, [26, 2], 8).kind).toBe("none");
  });
  it("falls back to the grid, measured from the origin of the drawing", () => {
    const o = { ...d, origin: [3, 3] as [number, number] };
    expect(snapEx(o, [58, 44], 2, { grid: 10 })).toEqual({ p: [63, 43], kind: "grid" });
  });
});

describe("locks", () => {
  it("lock and unlock elements, and a selection keeps only what is not locked", () => {
    let d = addLine(addNode(blank(), "CM", [0, 0]), "BN", [[0, 0], [10, 0]]);
    d = setLocked(d, [node("n1")], true);
    expect(isLocked(d, node("n1"))).toBe(true);
    expect(unlocked(d, [node("n1"), line("l1")])).toEqual([line("l1")]);
    expect(isLocked(setLocked(d, [node("n1")], false), node("n1"))).toBe(false);
  });
});

describe("splitting a line", () => {
  it("cuts it at the closest point and joins a node there", () => {
    const d = addLine(blank(), "CA", [[0, 0], [100, 0]]);
    const r = splitLineAt({ ...d, lines: [{ ...d.lines[0], circuit: "C-01" }] }, "l1", [40, 7], "CP");
    expect(r.drawing.lines.map((l) => l.points)).toEqual([[[0, 0], [40, 0]], [[40, 0], [100, 0]]]);
    expect(r.drawing.lines.map((l) => l.circuit)).toEqual(["C-01", "C-01"]);
    expect(r.drawing.nodes).toEqual([{ id: "n1", kind: "CP", x: 40, y: 0 }]);
    expect(r.lineId).toBe("l2");
  });
  it("does nothing at the end of a line", () => {
    const d = addLine(blank(), "CA", [[0, 0], [100, 0]]);
    expect(splitLineAt(d, "l1", [-5, 0]).drawing).toBe(d);
  });
});

describe("copy, paste and array", () => {
  const d = (() => { let x = addNode(blank(), "LU", [0, 0]); x = addLine(x, "CA", [[0, 0], [10, 0]]); return { ...x, nodes: [{ ...x.nodes[0], tag: "LU-001", circuit: "C-05" }] } as Drawing; })();
  const clip = copyElements(d, [node("n1"), line("l1")]);
  it("pastes copies with new ids, no tags and the same circuit", () => {
    const r = pasteClip(d, clip, [5, 5]);
    expect(r.refs).toEqual([node("n2"), line("l2")]);
    expect(r.drawing.nodes[1]).toMatchObject({ id: "n2", x: 5, y: 5, tag: "", circuit: "C-05" });
    expect(r.drawing.lines[1].points).toEqual([[5, 5], [15, 5]]);
    expect(copyElements(d, [node("n1")]).nodes[0]).not.toBe(d.nodes[0]);
  });
  it("makes a matrix of copies, each a step after the last", () => {
    const r = arrayClip(d, copyElements(d, [node("n1")]), 3, [30, 0]);
    expect(r.drawing.nodes.map((n) => n.x)).toEqual([0, 30, 60, 90]);
    expect(r.refs.length).toBe(3);
  });
  it("stores a template relative to its corner and without circuits", () => {
    const moved = pasteClip(blank(), clip, [100, 50]);
    const t = normalizeClip(copyElements(moved.drawing, moved.refs));
    expect(t.nodes[0]).toMatchObject({ x: 0, y: 0, tag: "" });
    expect(t.nodes[0].circuit).toBeUndefined();
    expect(t.lines[0].points).toEqual([[0, 0], [10, 0]]);
  });
});

describe("what is selected", () => {
  it("counts by kind, adds up the length in metres and lists the circuits", () => {
    let d = setScale(blank(), [0, 0], [100, 0], 10);
    d = addNode(addNode(d, "LU", [0, 0]), "LU", [5, 5]);
    d = addLine(addLine(d, "CA", [[0, 0], [30, 40]]), "CA", [[0, 0], [10, 0]]);
    d = { ...d, nodes: [{ ...d.nodes[0], circuit: "C-02" }, d.nodes[1]] };
    const s = selectionStats(d, [node("n1"), node("n2"), line("l1"), line("l2")], 0.1);
    expect(s).toEqual({ nodes: 2, lines: 2, byKind: { LU: 2, CA: 2 }, length_m: 6, circuits: ["C-02"] });
    expect(selectionStats(d, [line("l1")], null).length_m).toBeNull();
  });
  it("finds the box around some elements", () => {
    const d = addNode(addNode(blank(), "LU", [0, 0]), "LU", [100, 50]);
    expect(boundsOf(d, undefined, 0)).toEqual({ x: 0, y: 0, w: 100, h: 50 });
    expect(boundsOf(blank())).toBeNull();
  });
});

describe("align, distribute and transform", () => {
  const d = addNode(addNode(addNode(blank(), "LU", [0, 10]), "LU", [30, 40]), "LU", [100, 20]);
  const all = [node("n1"), node("n2"), node("n3")];
  it("aligns on a side or the middle", () => {
    expect(alignNodes(d, all, "left").nodes.map((n) => n.x)).toEqual([0, 0, 0]);
    expect(alignNodes(d, all, "bottom").nodes.map((n) => n.y)).toEqual([40, 40, 40]);
    expect(alignNodes(d, all, "hcenter").nodes.map((n) => n.x)).toEqual([50, 50, 50]);
    expect(alignNodes(d, [node("n1")], "left")).toBe(d);
  });
  it("spaces nodes evenly between the first and the last", () => {
    expect(distributeNodes(d, all, "x").nodes.map((n) => n.x)).toEqual([0, 50, 100]);
    expect(distributeNodes(d, [node("n1"), node("n2")], "x")).toBe(d);
  });
  it("rotates, mirrors and scales around the middle of the selection", () => {
    const e = addNode(addNode(blank(), "LU", [0, 0]), "LU", [10, 0]);
    const r = transformGroup(e, [node("n1"), node("n2")], { type: "rotate", deg: 90 });
    expect(r.nodes.map((n) => [Math.round(n.x), Math.round(n.y)])).toEqual([[5, -5], [5, 5]]);
    expect(transformGroup(e, [node("n1"), node("n2")], { type: "mirror", axis: "x" }).nodes.map((n) => n.x)).toEqual([10, 0]);
    expect(transformGroup(e, [node("n1"), node("n2")], { type: "scale", factor: 2 }).nodes.map((n) => n.x)).toEqual([-5, 15]);
    expect(transformGroup(e, [], { type: "scale", factor: 2 })).toBe(e);
  });
});

describe("measuring", () => {
  it("measures an angle and an area", () => {
    expect(measureAngle([10, 0], [0, 0], [0, 10])).toBeCloseTo(90);
    expect(measureAngle([10, 0], [0, 0], [-10, 0])).toBeCloseTo(180);
    expect(measureAngle([0, 0], [0, 0], [1, 1])).toBe(0);
    expect(polygonArea([[0, 0], [10, 0], [10, 5], [0, 5]])).toBe(50);
  });
  it("converts between the view and metres from the origin, y up", () => {
    const m = toMetres([30, 20], [10, 10], 0.5);
    expect(m).toEqual([10, -5]);
    expect(fromMetres(m, [10, 10], 0.5)).toEqual([30, 20]);
  });
  it("turns the underlay the shortest way to make a line horizontal or vertical", () => {
    expect(alignDelta([0, 0], [100, 10])).toBeCloseTo(-5.711, 2);
    expect(alignDelta([0, 0], [-100, -10])).toBeCloseTo(-5.711, 2);
    expect(alignDelta([0, 0], [10, 100], true)).toBeCloseTo(5.711, 2);
  });
});

describe("checks before making the files", () => {
  it("finds two nodes on top of each other, a node no cable reaches and a cable with no node", () => {
    let d = addNode(addNode(addNode(blank(), "CM", [0, 0]), "CM", [0.5, 0]), "CM", [200, 200]);
    d = addLine(addLine(d, "BN", [[0, 0], [50, 0]]), "BN", [[300, 300], [350, 300]]);
    const codes = findProblems(d, 2).map((p) => `${p.code}:${p.ref?.id}`);
    expect(codes).toContain("dup_node:n2");
    expect(codes).toContain("orphan_node:n3");
    expect(codes).toContain("isolated_line:l2");
    expect(codes.some((c) => c.endsWith("l1"))).toBe(false);
  });
  it("asks for a scale, a drawing and routes for the circuits", () => {
    const d = { ...blank(), circuits: [{ tag: "C-01", from: "n1", to: "n2", ternas: 1 }, { tag: "C-02", from: "n1", to: "n3", ternas: 1 }] };
    expect(generationChecks(d, {}, 2).map((p) => p.code)).toEqual(["no_scale", "empty", "circuit_unrouted", "circuit_unrouted"]);
    const ok = setScale(addLine(addNode(addNode(d, "TB", [0, 0]), "CM", [50, 0]), "BN", [[0, 0], [50, 0]]), [0, 0], [10, 0], 1);
    const p = generationChecks(ok, { "C-01": { found: true }, "C-02": { found: true, unreached: ["n3"] } }, 2);
    expect(p.map((x) => `${x.code}:${x.tag ?? ""}`)).toEqual(["circuit_open:C-02"]);
  });
});

describe("routes along the drawn network", () => {
  it("finds the shortest way through the lines, across a junction", () => {
    let d = addNode(addNode(blank(), "TB", [0, 0]), "LU", [100, 100]);
    d = addLine(d, "BN", [[0, 0], [100, 0], [100, 100]]);
    d = addLine(d, "BN", [[0, 0], [0, 100], [100, 100]]);
    d = addLine(d, "BN", [[50, 0], [50, 100]]);
    const r = shortestRoute(d, "n1", "n2", 1)!;
    expect(r.length).toBeCloseTo(200);
    expect(r.points[0]).toEqual([0, 0]);
    expect(r.points[r.points.length - 1]).toEqual([100, 100]);
  });
  it("is null when the nodes are not joined", () => {
    const d = addLine(addNode(addNode(blank(), "TB", [0, 0]), "LU", [100, 100]), "BN", [[0, 0], [50, 0]]);
    expect(shortestRoute(d, "n1", "n2", 1)).toBeNull();
    expect(shortestRoute(d, "n1", "zz", 1)).toBeNull();
  });
});

describe("labels and warnings", () => {
  it("moves a label that would lie on another and leaves the free ones", () => {
    const o = spreadLabels([{ id: "a", x: 0, y: 0, w: 40, h: 10 }, { id: "b", x: 5, y: 0, w: 40, h: 10 }, { id: "c", x: 200, y: 0, w: 40, h: 10 }]);
    expect(o.a).toEqual([0, 0]);
    expect(o.b).not.toEqual([0, 0]);
    expect(o.c).toEqual([0, 0]);
  });
  it("finds the elements a warning names by tag", () => {
    const nodes = [{ id: "n1", tag: "TB-001" }, { id: "n2", tag: "CM-001" }];
    const st = [{ line: "l1", tag: "CA-001/1", line_tag: "CA-001" }];
    expect(warningTargets("the loads of TB-001 are not routed along CA-001/1", nodes, st)).toEqual([node("n1"), line("l1")]);
    expect(warningTargets("something else", nodes, st)).toEqual([]);
  });
});
