import { describe, expect, it } from "vitest";
import { addLine, addNode, blank, Drawing, setScale } from "./planEditing";
import {
  addRoom, alignDelta, alignNodes, applyProposal, applyRuns, arrayClip, boundsOf, copyElements, distributeNodes, findProblems, fromMetres, generationChecks, inBoxCross, isLocked, measureAngle, normalizeClip, pasteClip,
  convertClip, linkProblems, insidePolygon, loadsByRoom, pointIndex, removeRoom, renameRoom, parallelToWall, wallFaces, wallSnap, polygonArea, selectionStats, setLocked, shortestRoute, snapEx, splitLineAt, spreadLabels, svgVertices, toMetres, transformGroup, unlocked, warningTargets,
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

describe("walls recognized in the plan", () => {
  const wall = { id: "w1", a: [0, 0] as [number, number], b: [100, 0] as [number, number], thickness: 10, confidence: 0.9 };
  it("has two faces, half the thickness either side of the centre line", () => {
    expect(wallFaces(wall)).toEqual([[[0, 5], [100, 5]], [[0, -5], [100, -5]]]);
  });
  it("snaps to a face, a corner winning over the middle of it, and to nothing when far", () => {
    expect(wallSnap([wall], [40, 9], 6)).toEqual([40, 5]);
    expect(wallSnap([wall], [3, 8], 6)).toEqual([0, 5]);
    expect(wallSnap([wall], [40, 30], 6)).toBeNull();
  });
  it("is one more thing snapEx looks at, after nodes and ends", () => {
    const d = addNode(blank(), "CM", [40, 5]);
    expect(snapEx(d, [41, 6], 5, { walls: [wall] }).kind).toBe("node");
    expect(snapEx(blank(), [41, 6], 5, { walls: [wall] })).toEqual({ p: [41, 5], kind: "wall" });
  });
  it("turns a line that is nearly parallel to a nearby wall into one that is", () => {
    const p = parallelToWall([0, 20], [100, 24], [wall], 30);
    expect(p[1]).toBeCloseTo(20, 5);
    expect(p[0]).toBeCloseTo(100.0, 0);
    expect(parallelToWall([0, 20], [100, 60], [wall], 80)).toEqual([100, 60]);          // too far from parallel
    expect(parallelToWall([0, 20], [100, 24], [wall], 5)).toEqual([100, 24]);           // no wall within reach
  });
});

describe("selecting by crossing", () => {
  it("takes what the box touches, not only what lies inside it", () => {
    let d = addNode(blank(), "LU", [10, 10]);
    d = addLine(d, "CA", [[-50, 5], [100, 5]]);
    d = addLine(d, "CA", [[0, 200], [100, 200]]);
    expect(inBoxCross(d, [0, 0], [20, 20])).toEqual([node("n1"), line("l1")]);
  });
});

describe("vertices of a vector underlay", () => {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><line x1="0" y1="0" x2="100" y2="50"/><polyline points="10,10 20,10 20,20"/><path d="M5 5 L15 5"/><path d="M0 0 C1 1 2 2 3 3"/></svg>';
  it("maps the points of lines, polylines and straight paths to the size the picture has on the view", () => {
    const v = svgVertices(svg, 200, 100);
    expect(v).toContainEqual([0, 0]);
    expect(v).toContainEqual([200, 100]);
    expect(v).toContainEqual([40, 20]);
    expect(v).toContainEqual([10, 10]);
    expect(v.length).toBe(7);                                                 // the curve gives none
  });
  it("gives nothing for text that is not an svg", () => {
    expect(svgVertices("not xml", 10, 10)).toEqual([]);
    expect(svgVertices("<html/>", 10, 10)).toEqual([]);
  });
  it("finds the nearest point within a distance without scanning all of them", () => {
    const near = pointIndex([[0, 0], [100, 100], [103, 100]], 20);
    expect(near([101, 101], 5)).toEqual([100, 100]);
    expect(near([50, 50], 5)).toBeNull();
    expect(near([102.4, 100], 5)).toEqual([103, 100]);
  });
});

describe("the same group on another level", () => {
  it("moves a clip between sheets with different origin and scale through metres", () => {
    const from = { origin: [0, 0] as [number, number], k: 0.1 }, to = { origin: [50, 50] as [number, number], k: 0.05 };
    const clip = { nodes: [{ id: "n1", kind: "LU", x: 100, y: 0 }], lines: [{ id: "l1", kind: "CA", points: [[0, 0], [100, 0]] as [number, number][] }] };
    const c = convertClip(clip, from, to);
    expect(c.nodes[0]).toMatchObject({ x: 250, y: 50 });                      // 10 m to the right of the origin, at the new scale
    expect(c.lines[0].points).toEqual([[50, 50], [250, 50]]);
  });
  it("checks that linked shafts exist, sit together and point back", () => {
    const here = { ...addNode(setScale(blank(), [0, 0], [100, 0], 10), "PL", [100, 100]), };
    const linked = { ...here, nodes: [{ ...here.nodes[0], attrs: { enlace: "L1:n1" } }] };
    const twin = (x: number, back: string) => ({ ...setScale(blank(), [0, 0], [100, 0], 10), nodes: [{ id: "n1", kind: "PL", x, y: 100, attrs: back ? { enlace: back } : undefined }] });
    const k = 0.1;
    expect(linkProblems(linked, "L0", k, () => undefined).map((p) => p.code)).toEqual(["link_missing"]);
    expect(linkProblems(linked, "L0", k, () => ({ drawing: twin(100, "L0:n1"), k })).map((p) => p.code)).toEqual([]);
    expect(linkProblems(linked, "L0", k, () => ({ drawing: twin(100, ""), k })).map((p) => p.code)).toEqual(["link_oneway"]);
    expect(linkProblems(linked, "L0", k, () => ({ drawing: twin(160, "L0:n1"), k })).map((p) => p.code)).toEqual(["link_far"]);
    expect(linkProblems(here, "L0", k, () => undefined)).toEqual([]);
  });
});

describe("rooms and the automatic design", () => {
  const square: [number, number][] = [[0, 0], [100, 0], [100, 100], [0, 100]];
  it("keeps rooms with a name, renames and removes them, and refuses an outline with fewer than three points", () => {
    let d = addRoom(blank(), "Cocina", square);
    d = addRoom(d, "Living", [[200, 0], [300, 0], [300, 100]]);
    expect((d.rooms ?? []).map((r) => [r.id, r.name])).toEqual([["r1", "Cocina"], ["r2", "Living"]]);
    expect(addRoom(d, "x", [[0, 0], [1, 1]])).toBe(d);
    expect(renameRoom(d, "r1", "Office").rooms?.[0].name).toBe("Office");
    expect(removeRoom(d, "r1").rooms?.map((r) => r.id)).toEqual(["r2"]);
  });
  it("tells which loads lie in which room, the smallest one winning, and which in none", () => {
    let d = addRoom(addRoom(blank(), "Grande", [[0, 0], [100, 0], [100, 100], [0, 100]]), "Chico", [[10, 10], [30, 10], [30, 30], [10, 30]]);
    d = addNode(addNode(addNode(addNode(d, "LU", [20, 20]), "LU", [60, 60]), "TG", [60, 70]), "LU", [500, 500]);
    expect(loadsByRoom(d, new Set(["LU", "TG"]))).toEqual({ rooms: { r2: { LU: 1 }, r1: { LU: 1, TG: 1 } }, outside: 1 });
    expect(insidePolygon([50, 50], square)).toBe(true);
    expect(insidePolygon([150, 50], square)).toBe(false);
  });
  it("applies the accepted runs: a tray per trunk and a conduit per stub", () => {
    const runs = { orientation: "horizontal", warnings: [], stats: {}, lines: [{ kind: "BN", points: [[0, 0], [50, 0]] as [number, number][], role: "trunk" as const }, { kind: "CN", points: [[50, 0], [50, 20]] as [number, number][], role: "stub" as const }] };
    expect(applyRuns(blank(), runs).lines.map((l) => [l.id, l.kind])).toEqual([["l1", "BN"], ["l2", "CN"]]);
  });
  it("applies an accepted wiring: circuits and the circuit of each load, without repeating a circuit already there", () => {
    const d = addNode(addNode(blank(), "TB", [0, 0]), "LU", [50, 0]);
    const proposal = { board: "n1", unassigned: [], warnings: [], limits: {}, routes: {}, assignments: { n2: "IUG-01" },
      circuits: [{ tag: "IUG-01", family: "IUG", room: "r1", room_name: "Cocina", loads: ["n2"], outlets: 1, from: "n1", to: "n2", via: [], ternas: 1, va: 100, va_per_outlet: 100, description: "" }],
    };
    const r = applyProposal(d, proposal);
    expect(r.nodes[1].circuit).toBe("IUG-01");
    expect(r.circuits).toEqual([{ tag: "IUG-01", from: "n1", to: "n2", via: [], ternas: 1 }]);
    expect(applyProposal(r, proposal).circuits).toHaveLength(1);
  });
});
