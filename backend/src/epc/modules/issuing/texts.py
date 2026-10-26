"""Wording of the delivery documents: the email message and the transmittal document. Formal technical register, third person, no greetings in the document.

To change a template edit the strings here; both languages follow the project locale (`es*` -> Spanish, anything else -> English).
"""
from typing import Dict, List

from epc.core import lang as lang_mod

EMISSION_NAMES = {
    "es": {"IFA": "Emitido para Aprobación", "IFC": "Emitido para Construcción", "AS-BUILT": "Conforme a Obra"},
    "en": {"IFA": "Issued for Approval", "IFC": "Issued for Construction", "AS-BUILT": "As-Built"},
}
DISCIPLINES = {
    "es": {"electrical": "Eléctrica", "civil": "Civil", "hvac": "HVAC", "fire": "Contra incendio", "mechanical": "Mecánica", "instrumentation": "Instrumentación",
           "telecom": "Telecomunicaciones", "general": "General"},
    "en": {"electrical": "Electrical", "civil": "Civil", "hvac": "HVAC", "fire": "Fire protection", "mechanical": "Mechanical", "instrumentation": "Instrumentation",
           "telecom": "Telecommunications", "general": "General"},
}

T: Dict[str, Dict[str, str]] = {
    "es": {
        "doc.title": "TRANSMITTAL", "doc.project": "Proyecto", "doc.client": "Cliente", "doc.issuer": "Emitido por", "doc.emission": "Emisión",
        "doc.client_rev": "Revisión del cliente", "doc.internal_rev": "Revisión interna", "doc.date": "Fecha de emisión",
        "doc.col.n": "N°", "doc.col.code": "Código", "doc.col.name": "Descripción", "doc.col.disc": "Disciplina", "doc.col.fmt": "Formatos",
        "doc.notes": "Observaciones", "doc.total": "Total", "doc.documents": "documentos", "doc.files": "archivos",
        "doc.integrity": "La integridad de cada archivo puede verificarse con la huella SHA-256 consignada en el archivo INDICE.csv del paquete.",
        "doc.page": "Página {n} de {total}", "doc.footer": "Transmittal {tr} · {project}",
        "mail.subject": "[{code}] Transmittal {tr} – {emission} {rev} – {project}",
        "mail.greeting": "Estimado equipo de {client}:",
        "mail.intro": "Nos dirigimos a ustedes para hacer entrega del transmittal {tr}, correspondiente a la emisión {emission} ({emission_name}), revisión {rev}, del proyecto «{project}» (código: {code}).",
        "mail.list": "Esta entrega incluye los siguientes documentos técnicos:",
        "mail.item": "* {code} – {name} (Formatos: {formats})",
        "mail.notes": "Observaciones de la emisión: {notes}",
        "mail.package": "Los archivos se encuentran adjuntos en el contenedor comprimido «{zip}». Dentro del mismo, encontrarán el documento formal de transmittal con el desglose del contenido y un archivo de índice que detalla la huella SHA-256 de cada elemento para garantizar su integridad.",
        "mail.request": "Agradecemos de antemano acusar recibo de este envío y solicitamos nos compartan sus observaciones dentro del plazo contractual acordado.",
        "mail.close": "{issuer} queda a su entera disposición para resolver cualquier duda o aclaración.",
        "mail.sign": "Atentamente,",
        "issuer.default": "La oficina de ingeniería", "client.default": "equipo", "signature.default": "[Nombre / Firma]",
    },
    "en": {
        "doc.title": "TRANSMITTAL", "doc.project": "Project", "doc.client": "Client", "doc.issuer": "Issued by", "doc.emission": "Issue",
        "doc.client_rev": "Client revision", "doc.internal_rev": "Internal revision", "doc.date": "Issue date",
        "doc.col.n": "No.", "doc.col.code": "Code", "doc.col.name": "Description", "doc.col.disc": "Discipline", "doc.col.fmt": "Formats",
        "doc.notes": "Remarks", "doc.total": "Total", "doc.documents": "documents", "doc.files": "files",
        "doc.integrity": "The integrity of each file can be verified with the SHA-256 hash listed in the INDICE.csv file of the package.",
        "doc.page": "Page {n} of {total}", "doc.footer": "Transmittal {tr} · {project}",
        "mail.subject": "[{code}] Transmittal {tr} – {emission} {rev} – {project}",
        "mail.greeting": "Dear {client} team,",
        "mail.intro": "We are writing to deliver transmittal {tr}, for issue {emission} ({emission_name}), revision {rev}, of the project \"{project}\" (code: {code}).",
        "mail.list": "This delivery includes the following technical documents:",
        "mail.item": "* {code} – {name} (Formats: {formats})",
        "mail.notes": "Remarks on the issue: {notes}",
        "mail.package": "The files are attached in the compressed package \"{zip}\". Inside it you will find the formal transmittal document with the breakdown of the contents and an index file listing the SHA-256 hash of each item to guarantee its integrity.",
        "mail.request": "We kindly ask you to acknowledge receipt of this delivery and to share your comments within the agreed contractual period.",
        "mail.close": "{issuer} remains at your disposal for any question or clarification.",
        "mail.sign": "Kind regards,",
        "issuer.default": "The engineering office", "client.default": "client", "signature.default": "[Name / Signature]",
    },
}


def lang_of(locale: str) -> str:
    return lang_mod.from_locale(locale)


def _disc(it: dict) -> str:
    return it.get("discipline") or it.get("source", "").split("/")[0]


def _fmt(files: List[dict]) -> str:
    return ", ".join(f["format"].upper() for f in files)


def email(lang: str, tr: dict, project: dict, zip_name: str, issuer: str) -> dict:
    t = T[lang]
    em = tr["emission"].upper()
    rev = f"Rev {tr['client_rev']}"
    ctx = dict(tr=tr["id"], emission=em, emission_name=EMISSION_NAMES[lang].get(em, em), rev=rev, project=project["name"], code=project["code"],
               client=project["client"] or t["client.default"])
    lines = [t["mail.greeting"].format(**ctx), "", t["mail.intro"].format(**ctx), "", t["mail.list"], ""]
    lines += [t["mail.item"].format(code=it["code"], name=it["name"], formats=_fmt(it["files"])) for it in tr["items"]]
    if tr.get("notes"):
        lines += ["", t["mail.notes"].format(notes=tr["notes"])]
    lines += ["", t["mail.package"].format(zip=zip_name), "", t["mail.request"], "",
              t["mail.close"].format(issuer=t["issuer.default"]), t["mail.sign"], "", issuer or t["signature.default"]]
    return {"subject": t["mail.subject"].format(**ctx), "body": "\n".join(lines), "language": lang}


def document(lang: str, tr: dict, project: dict, issuer: str) -> dict:
    """Data for epc_drawing.export.transmittal_pdf (a delivery note: facts and the list, no greetings)."""
    t = T[lang]
    em = tr["emission"].upper()
    files = sum(len(it["files"]) for it in tr["items"])
    disc = DISCIPLINES[lang]
    header = [[t["doc.project"], f"{project['name']} ({project['code']})"], [t["doc.client"], project["client"] or "-"], [t["doc.issuer"], issuer or t["issuer.default"]],
              [t["doc.emission"], f"{em} – {EMISSION_NAMES[lang].get(em, em)}"], [t["doc.client_rev"], f"Rev {tr['client_rev']}"],
              [t["doc.internal_rev"], tr["internal_rev"]], [t["doc.date"], tr["created"][:10]]]
    rows = [[str(i), it["code"], it["name"], disc.get(_disc(it), _disc(it)), _fmt(it["files"])] for i, it in enumerate(tr["items"], 1)]
    sections = []
    if tr.get("notes"):
        sections.append([t["doc.notes"], tr["notes"]])
    sections.append([t["doc.total"], f"{len(tr['items'])} {t['doc.documents']} · {files} {t['doc.files']}\n{t['doc.integrity']}"])
    return {"title": t["doc.title"], "subtitle": tr["id"], "header": header,
            "columns": [[t["doc.col.n"], 0.06], [t["doc.col.code"], 0.24], [t["doc.col.name"], 0.38], [t["doc.col.disc"], 0.16], [t["doc.col.fmt"], 0.16]],
            "rows": rows, "sections": sections, "footer": t["doc.footer"].format(tr=tr["id"], project=project["code"]), "page_label": t["doc.page"]}
