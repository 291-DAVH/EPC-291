import { describe, expect, it } from "vitest";
import { ENGINEER_TABS, placeOf, TABS } from "./tabs";

describe("where the screens that were tabs live now", () => {
  it("the drawings and the registers are no longer tabs of their own", () => {
    expect(TABS as readonly string[]).not.toContain("layout");
    expect(TABS as readonly string[]).not.toContain("registers");
    expect(ENGINEER_TABS).toEqual(["engineering", "coordination", "catalogs"]);
  });

  it("an old link to the drawings or the registers lands on the section that holds them", () => {
    expect(placeOf("layout", null)).toEqual({ tab: "engineering", sub: "layout" });
    expect(placeOf("registers", null)).toEqual({ tab: "plan", sub: "registers" });
  });

  it("any other link keeps its tab and section", () => {
    expect(placeOf("engineering", "sld")).toEqual({ tab: "engineering", sub: "sld" });
    expect(placeOf("plan", null)).toEqual({ tab: "plan", sub: null });
    expect(placeOf(null, null)).toEqual({ tab: null, sub: null });
  });
});
