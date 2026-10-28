import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "@epc/ui";
import AutoDesignDialog from "./AutoDesignDialog";
import type { Sizing } from "./autoDesign";
import type { AutoStage } from "./useAutoDesign";

afterEach(cleanup);

const sizing: Sizing = {
  containers: [{ line: "l1", tag: "CN-1", kind: "CN", circuits: ["IUG-01"], cables: 1, size: { diametro_mm: 20 }, used_pct: 40, limit_pct: 53, cable_mm: [10.5], fits: true },
               { line: "l2", tag: "BN-1", kind: "BN", circuits: ["IUG-01", "IUG-02"], cables: 2, size: { ancho_mm: 100, alto_mm: 50 }, used_pct: 60, limit_pct: 50, cable_mm: [10.5, 13.5], fits: false }],
  circuits: [{ tag: "IUG-01", section_mm2: 2.5, in_a: 16, du_pct: 1.2, complies: true, length_m: 20, plenums: ["PL1"], rise_m: 3, found: true }, { tag: "IUG-02", section_mm2: null, plenums: [], rise_m: 0, found: false }],
  warnings: ["one board could not be calculated"],
};

const show = (stage: AutoStage) => {
  const fns = { onRuns: vi.fn(), onWiring: vi.fn(), onApprove: vi.fn(), onClose: vi.fn() };
  render(<I18nProvider><AutoDesignDialog stage={stage} {...fns} /></I18nProvider>);
  return fns;
};

describe("automatic design dialog", () => {
  it("shows nothing when the design is not running", () => {
    show(null);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("offers the proposed route with what it holds and takes the acceptance or the stop", () => {
    const f = show({ step: "runs", proposal: { orientation: "horizontal", lines: [], warnings: [], stats: { orientation: "horizontal", trunks: 5, stubs: 10, bends: 0, trunk_length: 30, stub_length: 17.3, in_metres: true } } });
    expect(screen.getByRole("dialog").textContent).toContain("5 bandeja(s)");
    expect(screen.getByRole("dialog").textContent).toContain("47.3 m");
    fireEvent.click(screen.getByRole("button", { name: "Aceptar recorrido" }));
    expect(f.onRuns).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Detener" }));
    expect(f.onClose).toHaveBeenCalledTimes(1);
  });

  it("gives the detail of cables, plenums and sizes, points at what needs a look and approves on request", () => {
    const f = show({ step: "sizing", sizing });
    const text = screen.getByRole("dialog").textContent ?? "";
    expect(text).toContain("PL1 (+3 m)");                               // the plenum the circuit goes through and the height it adds
    expect(text).toContain("Ø20");
    expect(text).toContain("100×50");
    expect(text).toContain("IUG-02");                                   // no cable, no route
    expect(screen.getByRole("alert").textContent).toContain("BN-1");    // nothing holds it within its limit
    expect(text).toContain("one board could not be calculated");
    fireEvent.click(screen.getByRole("button", { name: "Aprobar y actualizar" }));
    expect(f.onApprove).toHaveBeenCalledTimes(1);
  });

  it("explains why it stopped, in the words of the person when there is no board on the plan", () => {
    show({ step: "stop", why: "noBoard" });
    expect(screen.getByRole("dialog").textContent).toContain("símbolo del tablero");
  });
});
