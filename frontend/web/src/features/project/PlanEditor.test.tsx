import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import PlanEditor, { Profile } from "./PlanEditor";
import { blank, Drawing, Ref } from "./planEditing";

/** The editor as a person uses it: tools, clicks, keys and menus over a canvas. jsdom has no layout, so the browser's matrix of the SVG is replaced by the identity: a click at (x, y) lands on (x, y) of the view. */
const PROFILE: Profile = {
  id: "electrica_BT", name: { es: "Eléctrica", en: "Electrical" }, shortcuts: { l: "LU", b: "BN" },
  nodes: [{ id: "LU", etiqueta: { es: "Luminaria", en: "Luminaire" }, prefijo_tag: "LU", simbolo_2d: "luminaria", capa_dxf: "ELEC", carga: true }, { id: "CP", etiqueta: { es: "Caja", en: "Box" }, prefijo_tag: "CP", simbolo_2d: "caja_pase", capa_dxf: "ELEC" }],
  lines: [{ id: "BN", etiqueta: { es: "Bandeja", en: "Tray" }, prefijo_tag: "BN", simbolo_2d: "linea_simple", capa_dxf: "ELEC" }],
};

beforeAll(() => {
  class FakePointer extends MouseEvent {
    pointerId: number; pointerType: string;
    constructor(type: string, init: PointerEventInit = {}) { super(type, init); this.pointerId = init.pointerId ?? 1; this.pointerType = init.pointerType ?? "mouse"; }
  }
  (window as unknown as { PointerEvent: unknown }).PointerEvent = FakePointer;
  const proto = SVGSVGElement.prototype as unknown as Record<string, unknown>;
  proto.getScreenCTM = () => ({ a: 1, d: 1, e: 0, f: 0, inverse: () => ({}) });
  proto.createSVGPoint = () => ({ x: 0, y: 0, matrixTransform() { return { x: (this as { x: number }).x, y: (this as { y: number }).y }; } });
  window.localStorage.clear();
});
afterEach(() => { cleanup(); window.localStorage.clear(); });

let latest: Drawing = blank();
let chosen: Ref[] = [];

function Harness({ start = blank(), readOnly = false }: { start?: Drawing; readOnly?: boolean }) {
  const [d, setD] = useState(start);
  const [sel, setSel] = useState<Ref[]>([]);
  latest = d; chosen = sel;
  return <PlanEditor drawing={d} onChange={setD} derived={null} profile={PROFILE} lang="es" underlayUrl={null} readOnly={readOnly} t={(k) => k} selection={sel} onSelect={setSel} />;
}

const svgOf = (c: HTMLElement) => c.querySelector("svg[preserveAspectRatio]") as SVGSVGElement;
const down = (el: Element, x: number, y: number, extra: object = {}) => act(() => { fireEvent(el, new PointerEvent("pointerdown", { clientX: x, clientY: y, button: 0, bubbles: true, ...extra })); });
const move = (el: Element, x: number, y: number, extra: object = {}) => act(() => { fireEvent(el, new PointerEvent("pointermove", { clientX: x, clientY: y, bubbles: true, ...extra })); });
const up = (el: Element, x: number, y: number) => act(() => { fireEvent(el, new PointerEvent("pointerup", { clientX: x, clientY: y, bubbles: true })); });
const tool = (name: string) => fireEvent.click(screen.getByTitle(new RegExp(`^plan\\.tool\\.${name}`)));
const key = (el: Element, k: string, extra: object = {}) => fireEvent.keyDown(el, { key: k, ...extra });

describe("plan editor: drawing", () => {
  it("places the chosen node where the canvas is clicked and takes it back with undo", () => {
    const { container } = render(<Harness />);
    tool("node");
    down(svgOf(container), 300, 200);
    expect(latest.nodes).toMatchObject([{ kind: "LU", x: 300, y: 200 }]);
    fireEvent.click(screen.getByTitle(/^layout\.undo/));
    expect(latest.nodes).toEqual([]);
    fireEvent.click(screen.getByTitle(/^layout\.redo/));
    expect(latest.nodes).toHaveLength(1);
  });

  it("draws a line by clicking its points and pressing Enter; it keeps going from the last point until Esc", () => {
    const { container } = render(<Harness />);
    const editor = container.querySelector(".wb-editor")!;
    tool("line");
    down(svgOf(container), 100, 100); down(svgOf(container), 300, 100);
    key(editor, "Enter");
    expect(latest.lines).toHaveLength(1);
    expect(latest.lines[0].points).toEqual([[100, 100], [300, 100]]);
    down(svgOf(container), 300, 300);                                   // the next stretch starts at the end of the last one
    key(editor, "Enter");
    expect(latest.lines).toHaveLength(2);
    expect(latest.lines[1].points).toEqual([[300, 100], [300, 300]]);
  });

  it("snaps a new node onto an existing one", () => {
    const { container } = render(<Harness start={{ ...blank(), nodes: [{ id: "n1", kind: "CP", x: 500, y: 400 }] }} />);
    tool("node");
    down(svgOf(container), 503, 398);
    expect(latest.nodes[1]).toMatchObject({ x: 500, y: 400 });
  });

  it("does not let a read-only editor change the drawing", () => {
    const { container } = render(<Harness readOnly />);
    expect(screen.queryByTitle(/^plan\.tool\.node/)).toBeNull();
    down(svgOf(container), 300, 200);
    expect(latest.nodes).toEqual([]);
  });
});

describe("plan editor: selecting and editing", () => {
  const two: Drawing = { ...blank(), nodes: [{ id: "n1", kind: "LU", x: 100, y: 100 }, { id: "n2", kind: "LU", x: 200, y: 100 }] };

  it("selects by dragging a box, copies and pastes at the cursor, and deletes", () => {
    const { container } = render(<Harness start={two} />);
    const svg = svgOf(container), editor = container.querySelector(".wb-editor")!;
    down(svg, 50, 50); move(svg, 250, 150); up(svg, 250, 150);
    expect(chosen).toEqual([{ type: "node", id: "n1" }, { type: "node", id: "n2" }]);
    key(editor, "c", { ctrlKey: true });
    move(svg, 400, 400);
    key(editor, "v", { ctrlKey: true });
    expect(latest.nodes).toHaveLength(4);
    expect(latest.nodes[2]).toMatchObject({ x: 400, y: 400, tag: "" });
    key(editor, "Delete");
    expect(latest.nodes).toHaveLength(2);
  });

  it("moves a node by dragging it, and not when it is locked", () => {
    const { container } = render(<Harness start={two} />);
    const svg = svgOf(container);
    down(svg, 100, 100); move(svg, 130, 160); up(svg, 130, 160);
    expect(latest.nodes[0]).toMatchObject({ x: 130, y: 160 });
    const editor = container.querySelector(".wb-editor")!;
    key(editor, "l", { ctrlKey: true });                                  // lock what is selected
    expect(latest.nodes[0].attrs).toEqual({ locked: true });
    down(svg, 130, 160); move(svg, 10, 10); up(svg, 10, 10);
    expect(latest.nodes[0]).toMatchObject({ x: 130, y: 160 });
  });

  it("opens a context menu on right click with what can be done to the element", () => {
    const { container } = render(<Harness start={two} />);
    fireEvent.contextMenu(svgOf(container), { clientX: 100, clientY: 100 });
    expect(screen.getByRole("menu")).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /plan\.act\.copy/ })).toBeTruthy();
    fireEvent.click(screen.getByRole("menuitem", { name: /plan\.act\.delete/ }));
    expect(latest.nodes.map((n) => n.id)).toEqual(["n2"]);
  });

  it("moves the selection with the arrow keys", () => {
    const { container } = render(<Harness start={two} />);
    const svg = svgOf(container), editor = container.querySelector(".wb-editor")!;
    down(svg, 100, 100); up(svg, 100, 100);
    key(editor, "ArrowRight", { shiftKey: true });
    expect(latest.nodes[0].x).toBe(110);
  });
});

describe("plan editor: commands", () => {
  it("finds a command in the palette and runs it", () => {
    const { container } = render(<Harness />);
    const editor = container.querySelector(".wb-editor")!;
    key(editor, "k", { ctrlKey: true });
    const box = screen.getByRole("dialog", { name: "plan.palette" }).querySelector("input")!;
    fireEvent.change(box, { target: { value: "plan.tool.erase" } });
    expect(screen.getAllByRole("option")).toHaveLength(1);
    fireEvent.keyDown(box, { key: "Enter" });
    expect(screen.queryByRole("dialog", { name: "plan.palette" })).toBeNull();
    expect(screen.getByTitle(/^plan\.tool\.erase/).getAttribute("aria-pressed")).toBe("true");
  });

  it("changes tool with its own key, and a person can give a tool another key", () => {
    const { container } = render(<Harness />);
    const editor = container.querySelector(".wb-editor")!;
    key(editor, "6");
    expect(screen.getByTitle(/^plan\.tool\.line/).getAttribute("aria-pressed")).toBe("true");
    key(editor, "l");                                                    // the key of the luminaire kind of the discipline
    expect(screen.getByTitle(/^plan\.tool\.node/).getAttribute("aria-pressed")).toBe("true");
  });

  it("measures a distance in metres once the scale is known", () => {
    const calibrated = { ...blank(), scale: { p1: [0, 0] as [number, number], p2: [100, 0] as [number, number], distance_m: 10 } };
    const { container } = render(<Harness start={calibrated} />);
    tool("measure");
    down(svgOf(container), 0, 0); down(svgOf(container), 300, 400);
    expect(container.textContent).toContain("50.000 m");
  });
});
