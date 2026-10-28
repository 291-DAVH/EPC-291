import type { LightMap } from "./lightingApi";
import { cellsOf } from "./lightingApi";
import { contoursOf, levelsOf } from "./lightingTools";

const CELL = 10;                                      // pixels of a cell in the image

/** The illuminance map of a room as a PNG: its cells coloured from the lowest to the highest lux, the lines of equal level with their lux, and the scale. Downloaded by the person. */
export function exportMapPng(m: LightMap, name: string): void {
  const w = m.nx * CELL, h = m.ny * CELL, bar = 28;
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(w, 220);
  canvas.height = h + bar + 12;
  const g = canvas.getContext("2d");
  if (!g) return;
  g.fillStyle = "#ffffff";
  g.fillRect(0, 0, canvas.width, canvas.height);
  for (const c of cellsOf(m)) {
    g.fillStyle = `hsl(${Math.round(240 - 240 * c.t)} 80% 50%)`;
    g.fillRect(((c.x - m.x0) / m.dx) * CELL, ((c.y - m.y0) / m.dy) * CELL, CELL, CELL);
  }
  g.strokeStyle = "#111111";
  g.fillStyle = "#111111";
  g.font = "10px sans-serif";
  for (const level of levelsOf(m.min, m.max)) {
    g.beginPath();
    const lines = contoursOf(m, level);
    for (const [a, b] of lines) { g.moveTo(((a[0] - m.x0) / m.dx) * CELL, ((a[1] - m.y0) / m.dy) * CELL); g.lineTo(((b[0] - m.x0) / m.dx) * CELL, ((b[1] - m.y0) / m.dy) * CELL); }
    g.stroke();
    if (lines.length) g.fillText(`${level}`, ((lines[0][0][0] - m.x0) / m.dx) * CELL + 2, ((lines[0][0][1] - m.y0) / m.dy) * CELL - 2);
  }
  const gradient = g.createLinearGradient(0, 0, 200, 0);
  gradient.addColorStop(0, "hsl(240 80% 50%)");
  gradient.addColorStop(0.5, "hsl(120 80% 50%)");
  gradient.addColorStop(1, "hsl(0 80% 50%)");
  g.fillStyle = gradient;
  g.fillRect(0, h + 6, 200, 8);
  g.fillStyle = "#111111";
  g.fillText(`${m.min.toFixed(0)} lx`, 0, h + 26);
  g.fillText(`${m.max.toFixed(0)} lx`, 160, h + 26);
  canvas.toBlob((blob) => {
    if (!blob) return;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${name.replace(/[^A-Za-z0-9_.-]+/g, "_")}.png`;
    link.click();
    URL.revokeObjectURL(link.href);
  });
}
