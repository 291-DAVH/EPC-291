import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, useApi } from "./api";

function reply(status: number, body: unknown, jsonFails = false) {
  return vi.fn().mockResolvedValue({ status, ok: status >= 200 && status < 300, json: jsonFails ? () => Promise.reject(new Error("no body")) : () => Promise.resolve(body) });
}

describe("api()", () => {
  beforeEach(() => vi.stubGlobal("fetch", reply(200, { ok: true })));
  afterEach(() => vi.unstubAllGlobals());

  it("calls /api + path with the session cookie and returns the JSON", async () => {
    const f = reply(200, { a: 1 });
    vi.stubGlobal("fetch", f);
    expect(await api("/me")).toEqual({ a: 1 });
    expect(f).toHaveBeenCalledWith("/api/me", { credentials: "same-origin" });
  });

  it("passes the request options through", async () => {
    const f = reply(200, {});
    vi.stubGlobal("fetch", f);
    await api("/x", { method: "POST", body: "{}" });
    expect(f).toHaveBeenCalledWith("/api/x", { credentials: "same-origin", method: "POST", body: "{}" });
  });

  it("throws an ApiError with the status, the body and the field errors", async () => {
    vi.stubGlobal("fetch", reply(422, { detail: { errors: { email: "not a valid email address" } } }));
    const e = await api("/x").catch((x) => x);
    expect(e).toBeInstanceOf(ApiError);
    expect(e.status).toBe(422);
    expect(e.message).toBe("422");
    expect(e.fieldErrors).toEqual({ email: "not a valid email address" });
  });

  it("has no field errors when the body has none or cannot be read", async () => {
    vi.stubGlobal("fetch", reply(500, null, true));
    const e = await api("/x").catch((x) => x);
    expect(e.body).toBeNull();
    expect(e.fieldErrors).toEqual({});
  });

  it("announces an ended session on 401, except for the sign-in calls themselves", async () => {
    const heard = vi.fn();
    window.addEventListener("epc-unauthorized", heard);
    vi.stubGlobal("fetch", reply(401, {}));
    await api("/projects").catch(() => undefined);
    expect(heard).toHaveBeenCalledTimes(1);
    await api("/auth/login").catch(() => undefined);
    expect(heard).toHaveBeenCalledTimes(1);
    window.removeEventListener("epc-unauthorized", heard);
  });
});

describe("useApi()", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loads the data of a path", async () => {
    vi.stubGlobal("fetch", reply(200, { n: 5 }));
    const { result } = renderHook(() => useApi<{ n: number }>("/count"));
    await waitFor(() => expect(result.current.data).toEqual({ n: 5 }));
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it("does nothing while the path is null", () => {
    const f = reply(200, {});
    vi.stubGlobal("fetch", f);
    const { result } = renderHook(() => useApi<unknown>(null));
    expect(f).not.toHaveBeenCalled();
    expect(result.current).toEqual({ data: null, error: null, loading: false });
  });

  it("reports an error as text", async () => {
    vi.stubGlobal("fetch", reply(404, { detail: "nope" }));
    const { result } = renderHook(() => useApi<unknown>("/missing"));
    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.error).toContain("404");
    expect(result.current.data).toBeNull();
  });
});
