import { describe, expect, it } from "vitest";
import { NOTE_LAYERS, notesHidden } from "./planPrefs";

describe("the annotations of the architectural plan", () => {
  it("are all hidden in every discipline but architecture", () => {
    expect(notesHidden("electrica_BT", [])).toEqual(NOTE_LAYERS);
    expect(notesHidden("hvac", ["ARQ-COTAS"])).toEqual(NOTE_LAYERS);
  });

  it("are seen in architecture, except the layers the person hid", () => {
    expect(notesHidden("arquitectura", [])).toEqual([]);
    expect(notesHidden("arquitectura", ["ARQ-EJES", "ELEC"])).toEqual(["ARQ-EJES"]);
  });
});
