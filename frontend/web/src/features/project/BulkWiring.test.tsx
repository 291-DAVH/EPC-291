import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "@epc/ui";
import BulkWiring, { KEEP, patchOf } from "./BulkWiring";

afterEach(cleanup);

const show = (onApply = vi.fn(), busy = false) => {
  const onClear = vi.fn();
  render(<I18nProvider><BulkWiring count={3} methods={["B1", "B2", "E"]} insulations={["pvc", "xlpe"]} materials={["cu", "al"]} defaults={{ material: "cu", insulation: "xlpe", method: "B2" }} busy={busy} onApply={onApply} onClear={onClear} /></I18nProvider>);
  return { onApply, onClear };
};
const pick = (label: RegExp, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } });

describe("changing the wiring of several circuits at once", () => {
  it("writes only what was changed: an untouched field stays and an empty one means the project criteria", () => {
    expect(patchOf(KEEP, KEEP, KEEP)).toEqual({});
    expect(patchOf("E", KEEP, "")).toEqual({ method: "E", material: "" });
    expect(patchOf("B2", "pvc", "al")).toEqual({ method: "B2", insulation: "pvc", material: "al" });
  });

  it("says how many circuits are selected and has nothing to apply until something is chosen", () => {
    const { onApply } = show();
    expect(screen.getByRole("group").textContent).toContain("3 circuito(s) seleccionado(s)");
    const apply = screen.getByRole("button", { name: "Aplicar a los seleccionados" }) as HTMLButtonElement;
    expect(apply.disabled).toBe(true);
    pick(/Instalación/, "E");
    expect(apply.disabled).toBe(false);
    fireEvent.click(apply);
    expect(onApply).toHaveBeenCalledWith({ method: "E" });
  });

  it("offers the project criteria with the value it stands for, and lets the selection go", () => {
    const { onApply, onClear } = show();
    expect(screen.getByLabelText(/Aislación/).textContent).toContain("Criterio del proyecto (XLPE)");
    pick(/Conductor/, "");
    pick(/Aislación/, "pvc");
    fireEvent.click(screen.getByRole("button", { name: "Aplicar a los seleccionados" }));
    expect(onApply).toHaveBeenCalledWith({ insulation: "pvc", material: "" });
    fireEvent.click(screen.getByRole("button", { name: "Quitar la selección" }));
    expect(onClear).toHaveBeenCalled();
  });

  it("does not apply while the board is working", () => {
    show(vi.fn(), true);
    pick(/Instalación/, "E");
    expect((screen.getByRole("button", { name: "Aplicar a los seleccionados" }) as HTMLButtonElement).disabled).toBe(true);
  });
});
