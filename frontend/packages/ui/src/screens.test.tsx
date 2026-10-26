import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CalcView } from "./api";
import { CalculationTable } from "./calculation";
import CompanySignup from "./CompanySignup";
import { I18nProvider } from "./i18n";

const wrap = (node: React.ReactNode) => render(<I18nProvider>{node}</I18nProvider>);

describe("CalculationTable", () => {
  const view: CalcView = {
    summary: { circuits: 3, compliant: 2, non_compliant: 1 },
    criteria: { limits_pct: { seccional: 1, terminal: 3, motor: 5 }, conductor: { material: "al", aislacion: "xlpe" }, rcd_ma: 30 },
    rows: [
      { tag: "C-01", description: "Alimentador", In: 125, Ib: 100, icu: 25, S: 70, dU: 0.8, disp: "MCCB 125 A", tipo: "feeder", limite_pct: 1, cumple: true },
      { tag: "M-01", description: "Bomba", In: 32, Ib: 28, icu: 10, S: 6, dU: 4.9, disp: "Guardamotor", cumple: false },
      { tag: "X-01", description: "Sin dato", In: 10, Ib: 8, icu: 6, S: 2.5, dU: 1, disp: "MCB" },
    ],
  };

  it("shows the summary, the limits, the conductor and one row per circuit", () => {
    const { container } = wrap(<CalculationTable view={view} />);
    const text = container.textContent ?? "";
    expect(text).toContain("3 ");
    expect(text).toContain("Al XLPE");
    expect(text).toMatch(/1 %.*3 %.*5 %/);
    expect(container.querySelectorAll("tbody tr")).toHaveLength(3);
    expect(Array.from(container.querySelectorAll("tbody tr")).map((r) => r.querySelector("td")?.textContent)).toEqual(["C-01", "M-01", "X-01"]);
  });

  it("marks compliance with a tick, a cross, or nothing when unknown", () => {
    const { container } = wrap(<CalculationTable view={view} />);
    const last = Array.from(container.querySelectorAll("tbody tr")).map((r) => r.querySelector("td:last-child")?.textContent);
    expect(last).toEqual(["✓", "✗", ""]);
  });

  it("omits the summary, the limits and the non-compliant badge when there is none", () => {
    const { container } = wrap(<CalculationTable view={{ rows: [], criteria: null, summary: { circuits: 1, compliant: 1, non_compliant: 0 } }} />);
    expect(container.querySelectorAll("tbody tr")).toHaveLength(0);
    expect(container.textContent).not.toContain("Al ");
  });
});

describe("CompanySignup", () => {
  const countries = [{ code: "AR", name: { es: "Argentina", en: "Argentina" }, tax: { id: "CUIT", example: "30-12345678-9", hint: { es: "11 dígitos", en: "11 digits" } }, region: { es: "Provincia", en: "Province" }, postal: { label: { es: "CP", en: "ZIP" }, example: "5500" } }];

  function route(register: () => { status: number; body: unknown }) {
    const calls: { url: string; init?: RequestInit }[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      let status = 200;
      let body: unknown = {};
      if (url.startsWith("/api/auth/countries")) body = countries;
      else if (url.startsWith("/api/auth/terms")) body = { version: "v1", text: "Terms" };
      else if (url === "/api/auth/company/register") ({ status, body } = register());
      return { status, ok: status < 300, json: async () => body };
    }));
    return calls;
  }
  afterEach(() => vi.unstubAllGlobals());

  const fill = (label: RegExp | string, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } });

  it("loads the countries and terms and keeps the button off until the terms are accepted", async () => {
    route(() => ({ status: 200, body: {} }));
    const { container } = wrap(<CompanySignup onDone={() => undefined} onBack={() => undefined} />);
    await waitFor(() => expect(container.querySelector("select option")).not.toBeNull());
    expect((container.querySelector("select") as HTMLSelectElement).value).toBe("AR");
    expect(container.querySelector("button.primary")).toHaveProperty("disabled", true);
    fireEvent.click(container.querySelector("input[type=checkbox]")!);
    expect(container.querySelector("button.primary")).toHaveProperty("disabled", false);
  });

  it("shows the errors of each field returned by the server and sends the whole form", async () => {
    const calls = route(() => ({ status: 422, body: { detail: { errors: { tax_id: "invalid tax id", contact_email: "not a valid email address" } } } }));
    const { container } = wrap(<CompanySignup onDone={() => undefined} onBack={() => undefined} />);
    await waitFor(() => expect(container.querySelector("input[name], input")).not.toBeNull());
    await waitFor(() => expect(container.querySelectorAll("fieldset input").length).toBeGreaterThan(2));
    const inputs = Array.from(container.querySelectorAll("input:not([type=checkbox])")) as HTMLInputElement[];
    inputs.forEach((i, n) => fireEvent.change(i, { target: { value: i.type === "email" ? "a@b.com" : `v${n}` } }));
    fireEvent.click(container.querySelector("input[type=checkbox]")!);
    fireEvent.submit(container.querySelector("form")!);
    await waitFor(() => expect(container.querySelector(".err")).not.toBeNull());
    expect(Array.from(container.querySelectorAll(".err")).map((e) => e.textContent)).toEqual(expect.arrayContaining(["invalid tax id", "not a valid email address"]));
    const post = calls.find((c) => c.url === "/api/auth/company/register")!;
    const sent = JSON.parse(String(post.init?.body));
    expect(sent).toMatchObject({ country: "AR", accept_terms: true, terms_version: "v1", lang: "es" });
    expect(Object.keys(sent)).toEqual(expect.arrayContaining(["org_name", "tax_id", "street", "number", "locality", "region", "postal_code", "contact_email", "name", "username", "password"]));
  });

  it("moves to the code step when the registration is accepted", async () => {
    route(() => ({ status: 200, body: { registration: "r1", email: "j***@acme.com", expires_minutes: 15 } }));
    const { container } = wrap(<CompanySignup onDone={() => undefined} onBack={() => undefined} />);
    await waitFor(() => expect(container.querySelectorAll("fieldset input").length).toBeGreaterThan(2));
    fireEvent.click(container.querySelector("input[type=checkbox]")!);
    fireEvent.submit(container.querySelector("form")!);
    await waitFor(() => expect(container.textContent).toContain("j***@acme.com"));
    const code = container.querySelector("input[autocomplete=one-time-code]") as HTMLInputElement;
    fireEvent.change(code, { target: { value: "12ab34" } });
    expect(code.value).toBe("1234");                                             // only digits are kept
    expect(container.querySelector("button.primary")).toHaveProperty("disabled", true);
    fireEvent.change(code, { target: { value: "123456" } });
    expect(container.querySelector("button.primary")).toHaveProperty("disabled", false);
  });
});
