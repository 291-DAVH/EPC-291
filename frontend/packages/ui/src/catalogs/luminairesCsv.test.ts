import { describe, expect, it } from "vitest";
import { parseLuminaires } from "./luminairesCsv";

const HEADER = "id,name_es,name_en,kind,lamps,lamp_flux_lm,power_w,power_factor,group";

describe("luminaires from a spreadsheet", () => {
  it("reads commas, semicolons with decimal commas, and tabs copied from a sheet", () => {
    const commas = parseLuminaires(`${HEADER}\nmy_panel,Panel mio,My panel,interior,1,3600,36,0.9,Offices`);
    expect(commas.errors).toEqual([]);
    expect(commas.entries.my_panel).toEqual({ name: { es: "Panel mio", en: "My panel" }, kind: "interior", lamps: 1, lamp_flux_lm: 3600, power_w: 36, power_factor: 0.9, group: "Offices", illustrative: false });
    const semicolons = parseLuminaires("id;name_es;name_en;lamp_flux_lm;power_w;power_factor\nx;Uno;One;2500;20,5;0,95");
    expect(semicolons.entries.x).toMatchObject({ lamp_flux_lm: 2500, power_w: 20.5, power_factor: 0.95, kind: "interior", lamps: 1 });
    const tabs = parseLuminaires("id\tname_es\tname_en\tkind\tlamp_flux_lm\nf\tProyector\tFlood\texterior\t11000");
    expect(tabs.entries.f).toMatchObject({ kind: "exterior", power_w: null });
  });

  it("keeps quoted names with commas and drops the byte order mark and the empty lines", () => {
    const out = parseLuminaires(`\uFEFF${HEADER}\n\na,"Panel, grande",Big panel,interior,1,3000,30,,\n`);
    expect(out.entries.a.name.es).toBe("Panel, grande");
    expect(out.entries.a).not.toHaveProperty("power_factor");
    expect(out.entries.a).not.toHaveProperty("group");
  });

  it("says which row and what to correct, and still returns the rows that are fine", () => {
    const out = parseLuminaires([HEADER, "ok,Uno,One,interior,1,3000,30,,", "bad id,Dos,Two,interior,1,3000,30,,", "b,,Three,interior,1,3000,30,,", "c,Cuatro,Four,interior,1,0,30,,",
      "d,Cinco,Five,interior,1.5,3000,30,,", "e,Seis,Six,interior,1,3000,-1,,", "f,Siete,Seven,interior,1,3000,30,1.5,", "ok,Otra,Again,interior,1,3000,30,,"].join("\n"));
    expect(Object.keys(out.entries)).toEqual(["ok"]);
    expect(out.errors).toEqual(["3: id", "4: name_es / name_en", "5: lamp_flux_lm", "6: lamps", "7: power_w", "8: power_factor", "9: id (repeated)"]);
  });

  it("refuses a text without the columns that are needed or without anything", () => {
    expect(parseLuminaires("id,name_es\nx,Uno").errors).toEqual(["columns: name_en, lamp_flux_lm"]);
    expect(parseLuminaires("  \n").errors).toEqual(["empty"]);
  });
});
