import { useState } from "react";
import { Key, LayersEditor, LuminairesEditor, SolutionsEditor, useI18n } from "@epc/ui";

type Sub = "layers" | "solutions" | "luminaires";

/** The catalogs of drawing of this project: DXF layers and standard solutions. They start as the company's (and the MASTER's); what is changed here applies to this project only. */
export default function Catalogs({ client, code }: { client: string; code: string }) {
  const { t } = useI18n();
  const [sub, setSub] = useState<Sub>("layers");
  const base = `/projects/${client}/${code}`;
  return (
    <>
      <p className="help">{t("catalogs.project.help")}</p>
      <div className="subtabs" role="tablist">
        {(["layers", "solutions", "luminaires"] as Sub[]).map((x) => (
          <button key={x} role="tab" aria-selected={sub === x} className={sub === x ? "on" : ""} onClick={() => setSub(x)}>{t(`catalogs.tab.${x}` as Key)}</button>
        ))}
      </div>
      {sub === "layers" && <LayersEditor bare path={`${base}/drawing-layers`} />}
      {sub === "solutions" && <SolutionsEditor bare path={`${base}/standard-solutions`} />}
      {sub === "luminaires" && <LuminairesEditor bare path={`${base}/lighting/luminaires`} />}
    </>
  );
}
