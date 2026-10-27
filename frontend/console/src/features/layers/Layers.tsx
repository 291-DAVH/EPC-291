import { LayersEditor } from "@epc/ui";

/** The MASTER's (global) catalog of DXF layers. */
export default function Layers() {
  return <LayersEditor path="/layers" />;
}
