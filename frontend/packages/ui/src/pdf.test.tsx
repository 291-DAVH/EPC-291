import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { I18nProvider } from "./i18n";
import { PdfViewer } from "./pdf";

const wrap = (node: React.ReactNode) => render(<I18nProvider>{node}</I18nProvider>);

describe("the PDF reader of the program", () => {
  const created: string[] = [], revoked: string[] = [];
  beforeEach(() => {
    created.length = 0; revoked.length = 0;
    URL.createObjectURL = vi.fn(() => { const u = `blob:pdf-${created.length}`; created.push(u); return u; });
    URL.revokeObjectURL = vi.fn((u: string) => { revoked.push(u); });
  });
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("fetches the file with the session and shows it from a local copy, with a way to open and download it", async () => {
    const fetchMock = vi.fn(async () => new Response(new Blob(["%PDF-1.4"]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    wrap(<PdfViewer path="/projects/A/B/engineering/pdf?path=x.pdf" title="LIGHTING_L0" />);
    const frame = await waitFor(() => screen.getByTitle("LIGHTING_L0") as HTMLIFrameElement);
    expect(fetchMock).toHaveBeenCalledWith("/api/projects/A/B/engineering/pdf?path=x.pdf", { credentials: "same-origin" });
    expect(frame.getAttribute("src")).toBe("blob:pdf-0#view=FitH");
    const links = screen.getAllByRole("link");
    expect(links.map((l) => l.getAttribute("href"))).toEqual(["blob:pdf-0", "blob:pdf-0"]);
    expect(links[1].getAttribute("download")).toBe("LIGHTING_L0.pdf");
  });

  it("does not add .pdf to a name that has it, and gives the copy back when it goes away", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(new Blob(["%PDF"]), { status: 200 })));
    const view = wrap(<PdfViewer path="/p" title="memoria.pdf" />);
    await waitFor(() => screen.getByTitle("memoria.pdf"));
    expect(screen.getAllByRole("link")[1].getAttribute("download")).toBe("memoria.pdf");
    view.unmount();
    expect(revoked).toEqual(["blob:pdf-0"]);
  });

  it("says the file could not be read, and reads another when the path changes", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("no", { status: 404 })));
    const view = wrap(<PdfViewer path="/missing" title="x" />);
    await waitFor(() => expect(document.querySelector(".state.err")?.textContent).toContain("404"));
    vi.stubGlobal("fetch", vi.fn(async () => new Response(new Blob(["%PDF"]), { status: 200 })));
    view.rerender(<I18nProvider><PdfViewer path="/there" title="x" /></I18nProvider>);
    await waitFor(() => screen.getByTitle("x"));
    expect(created).toHaveLength(1);
  });
});
