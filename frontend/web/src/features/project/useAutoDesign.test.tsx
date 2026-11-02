import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { blank } from "./planEditing";
import { useAutoDesign } from "./useAutoDesign";

const reply = (body: unknown) => Promise.resolve({ ok: true, status: 200, headers: { get: () => "application/json" }, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) });
const WIRING = { circuits: [{ tag: "TUG-01", description: "Oficina", va: 300, lines: [], loads: [] }], warnings: [], attach: [] };
const SIZING = { containers: [], circuits: [], warnings: [] };

let urls: string[] = [];
beforeEach(() => {
  urls = [];
  vi.stubGlobal("fetch", vi.fn((url: string) => {
    urls.push(url);
    return reply(url.endsWith("/design/wiring") ? WIRING : url.endsWith("/design/sizing") ? SIZING : {});
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

const drawn = { ...blank(), lines: [{ id: "l1", kind: "BN", points: [[0, 0], [10, 0]] as [number, number][] }] };

/** The design of an applied proposal, up to the approval of the sizing, with what the memo callback does. */
async function runThrough(memo?: () => Promise<void>) {
  const commit = vi.fn(() => Promise.resolve());
  const { result } = renderHook(() => useAutoDesign({ root: "/projects/A/P/layout", level: "L0", families: () => ({}), board: () => ({ node: "b1", id: "tgbt" }), commit, preview: () => undefined, memo }));
  await act(async () => { await result.current.start(drawn); });
  await act(async () => { await result.current.acceptWiring(); });
  await act(async () => { await result.current.approve((d) => d); });
  return { stage: result.current.stage, commit };
}

describe("the automatic design after the loads are on the plan", () => {
  it("goes from the circuits to the sizing and asks for the memo of the board when the sizes are approved", async () => {
    const memo = vi.fn(() => Promise.resolve());
    const { stage } = await runThrough(memo);
    expect(urls.map((u) => u.split("/design/")[1])).toEqual(["wiring", "circuits", "sizing"]);        // the runs were already drawn
    expect(memo).toHaveBeenCalledTimes(1);
    expect(stage).toEqual({ step: "done", memo: "started" });
  });

  it("finishes anyway when the memo cannot be asked for and says so", async () => {
    const { stage } = await runThrough(() => Promise.reject(new Error("no board")));
    expect(stage).toEqual({ step: "done", memo: "failed" });
  });

  it("does not mention a memo when the caller has none to ask for", async () => {
    expect((await runThrough()).stage).toEqual({ step: "done", memo: undefined });
  });
});
