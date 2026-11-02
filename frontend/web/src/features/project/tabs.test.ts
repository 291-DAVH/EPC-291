import { describe, expect, it } from "vitest";
import { ENGINEER_TABS, placeOf, TABS } from "./tabs";

describe("where the screens that were tabs live now", () => {
  it("the drawings, the registers and the deliverables are no longer tabs of their own", () => {
    expect(TABS as readonly string[]).not.toContain("deliverables");
    expect(TABS as readonly string[]).not.toContain("layout");
    expect(TABS as readonly string[]).not.toContain("registers");
    expect(ENGINEER_TABS).toEqual(["engineering"]);
    for (const gone of ["coordination", "catalogs", "observations"]) expect(TABS as readonly string[]).not.toContain(gone);
  });

  it("an old link to the drawings or the registers lands on the section that holds them", () => {
    expect(placeOf("layout", null)).toEqual({ tab: "engineering", sub: "layout" });
    expect(placeOf("registers", null)).toEqual({ tab: "plan", sub: "registers" });
    expect(placeOf("coordination", null)).toEqual({ tab: "engineering", sub: "coordination" });
    expect(placeOf("observations", null)).toEqual({ tab: "reports", sub: "observations" });
    expect(placeOf("engineering", "issue")).toEqual({ tab: "plan", sub: "issue" });
    expect(placeOf("engineering", "parties")).toEqual({ tab: "plan", sub: "team" });
    expect(placeOf("deliverables", null)).toEqual({ tab: "plan", sub: "deliverables" });
  });

  it("any other link keeps its tab and section", () => {
    expect(placeOf("engineering", "sld")).toEqual({ tab: "engineering", sub: "sld" });
    expect(placeOf("plan", null)).toEqual({ tab: "plan", sub: null });
    expect(placeOf(null, null)).toEqual({ tab: null, sub: null });
  });
});
