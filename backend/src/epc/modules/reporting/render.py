"""Renderings of a report document model: Markdown (the PDF is produced by the engine exporter from the same model)."""


def to_markdown(doc: dict) -> str:
    out = [f"# {doc['title']} — {doc['subtitle']}", ""]
    for b in doc["blocks"]:
        k = b["type"]
        if k == "kv":
            out += [f"**{label}:** {value}  " for label, value in b["rows"]] + [""]
        elif k == "h":
            out += [f"### {b['text']}", ""]
        elif k == "p":
            out += [b["text"], ""]
        elif k == "bullets":
            out += [f"- {i}" for i in b["items"]] + [""]
        elif k == "table":
            if not b["rows"]:
                out += [f"_{b['empty']}_" if b.get("empty") else "", ""]
                continue
            esc = lambda x: str(x).replace("|", "\\|").replace("\n", " ")
            out += ["| " + " | ".join(esc(c[0]) for c in b["columns"]) + " |", "|" + "|".join("---" for _ in b["columns"]) + "|"]
            out += ["| " + " | ".join(esc(x) for x in r) + " |" for r in b["rows"]] + [""]
    return "\n".join(out).rstrip("\n") + "\n"
