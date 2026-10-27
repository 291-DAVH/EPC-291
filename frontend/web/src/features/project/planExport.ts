/** Pictures of the canvas: a PNG to download and a printable sheet (the browser's own "save as PDF"). Both work from the SVG on the screen. */

/** The SVG as a standalone document: the underlay picture inlined (an SVG shown as an image cannot load anything outside itself) and a white page behind. */
async function standalone(svg: SVGSVGElement, underlayUrl: string | null, size: { w: number; h: number }): Promise<string> {
  const copy = svg.cloneNode(true) as SVGSVGElement;
  copy.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  copy.setAttribute("width", String(size.w));
  copy.setAttribute("height", String(size.h));
  copy.removeAttribute("style");
  copy.querySelectorAll("[data-ui]").forEach((el) => el.remove());              // handles, hover marks and other aids are not part of the drawing
  if (underlayUrl) {
    const blob = await (await fetch(underlayUrl)).blob();
    const data = await new Promise<string>((ok) => { const r = new FileReader(); r.onload = () => ok(String(r.result)); r.readAsDataURL(blob); });
    copy.querySelectorAll("image").forEach((im) => im.setAttribute("href", data));
  }
  const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x", copy.viewBox.baseVal.x.toString()); bg.setAttribute("y", copy.viewBox.baseVal.y.toString());
  bg.setAttribute("width", copy.viewBox.baseVal.width.toString()); bg.setAttribute("height", copy.viewBox.baseVal.height.toString()); bg.setAttribute("fill", "#fff");
  copy.insertBefore(bg, copy.firstChild);
  return new XMLSerializer().serializeToString(copy);
}

export async function exportPng(svg: SVGSVGElement, underlayUrl: string | null, name: string): Promise<void> {
  const box = svg.getBoundingClientRect();
  const scale = 2;
  const size = { w: Math.max(2, Math.round(box.width * scale)), h: Math.max(2, Math.round(box.height * scale)) };
  const text = await standalone(svg, underlayUrl, size);
  const img = new Image();
  const url = URL.createObjectURL(new Blob([text], { type: "image/svg+xml;charset=utf-8" }));
  await new Promise<void>((ok, bad) => { img.onload = () => ok(); img.onerror = () => bad(new Error("image")); img.src = url; });
  const canvas = document.createElement("canvas");
  canvas.width = size.w; canvas.height = size.h;
  canvas.getContext("2d")!.drawImage(img, 0, 0, size.w, size.h);
  URL.revokeObjectURL(url);
  const blob: Blob = await new Promise((ok, bad) => canvas.toBlob((b) => (b ? ok(b) : bad(new Error("png"))), "image/png"));
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = `${name}.png`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}

export interface SheetInfo { title: string; lines: string[] }

/** A page with the drawing and a title block, ready to print or save as PDF with the browser. */
export async function printSheet(svg: SVGSVGElement, underlayUrl: string | null, info: SheetInfo): Promise<void> {
  const box = svg.getBoundingClientRect();
  const text = await standalone(svg, underlayUrl, { w: Math.round(box.width), h: Math.round(box.height) });
  const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c] as string));
  const w = window.open("", "_blank", "noopener,width=1000,height=720");
  if (!w) throw new Error("popup");
  w.document.write(`<!doctype html><meta charset="utf-8"><title>${esc(info.title)}</title>
<style>@page{size:landscape;margin:10mm}body{margin:0;font:12px system-ui,sans-serif;color:#111}.sheet{border:2px solid #111;display:grid;grid-template-rows:1fr auto;height:calc(100vh - 8px)}
.draw{min-height:0;overflow:hidden}.draw svg{width:100%;height:100%;display:block}.block{display:flex;gap:24px;border-top:2px solid #111;padding:6px 10px}.block b{font-size:14px}</style>
<div class="sheet"><div class="draw">${text}</div><div class="block"><b>${esc(info.title)}</b>${info.lines.map((l) => `<span>${esc(l)}</span>`).join("")}</div></div>`);
  w.document.close();
  w.focus();
  setTimeout(() => w.print(), 300);
}
