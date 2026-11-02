import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "@epc/ui";
import Memos from "./Memos";

const BOARD = { id: "tgbt", name: "TGBT", voltage_v: 380, system: "TN-S", icc_ka: 10, circuits: 3, supplied_from: "", supply_tag: "", state: "idle" };
const MEMO = { available: true, stale: true, files: [], memo: null };

let calls: { url: string; method: string }[] = [];
let studyExists = true;

function reply(body: unknown, status = 200) {
  return Promise.resolve({ ok: status < 400, status, headers: { get: () => "application/json" }, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) });
}

beforeEach(() => {
  calls = [];
  vi.stubGlobal("fetch", vi.fn((url: string, init?: { method?: string }) => {
    calls.push({ url, method: init?.method ?? "GET" });
    if (url.includes("/sld/boards")) return reply([BOARD]);
    if (url.includes("/sld/memo")) return reply(MEMO);
    if (url.includes("/sld/calculation")) return reply({ rows: [{ tag: "C-01" }], criteria: null });
    if (url.includes("/sld/status")) return reply({ state: "done", outputs: [], log: [] });
    if (url.includes("/sld/generate")) return reply({ state: "running", outputs: [], log: [] }, 202);
    if (url.includes("/study") && url.includes("/remake")) return reply({ exists: true, stale: false });
    if (url.includes("/lighting/study") || url.includes("/receptacles/study")) return reply(studyExists ? { exists: true, stale: true, report: true, saved_at: "2026-11-01T10:00:00" } : { exists: false });
    if (url.includes("/layout")) return reply({ levels: [{ level: "L0@electrica_BT", discipline: "electrica_BT" }, { level: "L0", discipline: "arquitectura" }] });
    return reply({});
  }));
  studyExists = true;
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

const show = (canWrite = true) => render(<I18nProvider><Memos client="ACME" code="P-1" canWrite={canWrite} onOpenFiles={() => undefined} /></I18nProvider>);

describe("Memos: every generator in one place", () => {
  it("lists each board and each electrical sheet with the state of what is generated", async () => {
    show();
    await screen.findByText("TGBT");
    expect(await screen.findByText("Cables calculados")).toBeTruthy();
    expect(await screen.findByText("Memoria desactualizada")).toBeTruthy();
    expect(screen.getAllByText("L0@electrica_BT")).toHaveLength(2);                              // the lighting study and the socket outlets one
    expect(screen.queryByText("L0")).toBeNull();                                                  // the Architecture sheet has no study
    expect(screen.getAllByText("Estudio desactualizado")).toHaveLength(2);
  });

  const asks = async (button: string, wanted: (c: { url: string; method: string }) => boolean, nth = 0) => {
    show();
    await screen.findByText("TGBT");
    fireEvent.click(screen.getAllByRole("button", { name: button })[nth]);
    await waitFor(() => expect(calls.some((c) => c.method === "POST" && wanted(c))).toBe(true));
  };

  it("asks for the calculation alone with its own run", () => asks("Calcular cables y protecciones", (c) => c.url.includes("diagrams=calc")));
  it("asks for the memo and the summary with their own run", () => asks("Generar memoria y síntesis", (c) => c.url.includes("diagrams=none")));
  it("asks for the lighting study to be calculated again from the saved sheet", () => asks("Calcular y generar memoria", (c) => c.url.includes("/lighting/study/L0%40electrica_BT/remake?lang=es")));
  it("asks for the socket outlets study to be calculated again from the saved sheet", () => asks("Calcular y generar memoria", (c) => c.url.includes("/receptacles/study/L0%40electrica_BT/remake?lang=es"), 1));

  it("does not let someone who cannot write generate anything", async () => {
    show(false);
    await screen.findByText("TGBT");
    for (const name of ["Calcular cables y protecciones", "Generar memoria y síntesis", "Calcular y generar memoria"]) {
      for (const b of screen.getAllByRole("button", { name })) expect((b as HTMLButtonElement).disabled).toBe(true);
    }
  });
});
