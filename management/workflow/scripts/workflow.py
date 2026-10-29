#!/usr/bin/env python3
"""workflow.py — operaciones de flujo por ubicación (WF-001). Cada script de .claude/hooks es un
envoltorio de una función cli_* de este módulo. Ver fwlib.py para el modelo y las reglas.

Ningún script edita el contenido de un documento: mueve, copia, renombra y registra.
"""
import argparse
import json
import os
import re
import shutil

import fwlib as W
from fwlib import FwError

# --------------------------------------------------------------------------------- utilidades
def _raiz(args):
    return W.encontrar_raiz(args.root) if args.root else W.encontrar_raiz()


def _parser(desc):
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--root", help="raíz del proyecto (por defecto, la carpeta actual o la que la contiene)")
    return p


def _estado_doc(raiz, lme, pq, estado):
    if lme.filas:
        lme.poner(pq, "estado", W.ESTADO_DOC.get(estado, estado))


def _led_o_error(raiz, pq):
    led = W.leer_ledger(raiz, pq)
    if led is None:
        raise FwError(f"{pq} no tiene registro (nunca se envió a revisión).")
    return led


def _verificar_ubicacion(raiz, led, esperado):
    est, det = W.ubicaciones(raiz, led)
    if led["estado"] != esperado or est != esperado:
        raise FwError(f"{led['pq']} debería estar en {esperado}; registro: {led['estado']}, "
                      f"ubicación real: {est}{' (' + det + ')' if det else ''}. Ejecute CHECK_STATE.py.")
    dif = W.hash_ok(raiz, led, esperado)
    if dif:
        raise FwError(f"{led['pq']} fue modificado fuera de Ingeniería ({'; '.join(dif[:4])}). "
                      f"No puede avanzar: ejecute RETURN_TO_ENGINEERING.py {led['pq']} y rehaga el ciclo completo.")


# --------------------------------------------------------------------------------- SEND_TO_REVIEW
def send_to_review(raiz, pq, emision=None, extras=(), permitir_varios=None):
    pq = W.validar_pq(pq)
    lme = W.LME(raiz)
    led = W.leer_ledger(raiz, pq) or W.nuevo_ledger(pq)
    if led["estado"] != "ENGINEERING":
        raise FwError(f"{pq} ya está en {led['estado']}; para modificarlo use RETURN_TO_ENGINEERING.py.")
    emision = (emision or led["emision"] or lme.emision(pq) or "").upper()
    if emision not in W.EMISIONES:
        raise FwError(f"{pq}: indique la emisión objetivo con --emision ({', '.join(W.EMISIONES)}); la LME no la define.")
    W.exigir_fase(raiz, emision)                                     # un proyecto que termina antes no prepara las emisiones que vienen después
    for dep in lme.dependencias(pq):
        d = W.leer_ledger(raiz, dep)
        if d is None or d["estado"] == "ENGINEERING":
            raise FwError(f"{pq} depende de {dep}, que sigue en Ingeniería (o nunca se envió a revisión).")
        if d["estado"] == "FOR_REVIEW":
            h = W.hoja_vigente(raiz, dep)
            if not h or h[1] != "APPROVED":
                raise FwError(f"{pq} depende de {dep}, que todavía no está REVIEWED (su hoja de revisión no dice «Resultado: APPROVED»).")
    otros = [q for q, l in W.todos_los_ledgers(raiz).items() if l["estado"] == "FOR_REVIEW" and q != pq]
    if otros and not permitir_varios:
        raise FwError(f"Ya hay un paquete en FOR_REVIEW ({', '.join(otros)}). Solo uno a la vez, salvo DEC registrada "
                      "(use --permitir-varios DEC-nnn).")
    if permitir_varios:
        W.validar_dec_existe(raiz, permitir_varios)  # A1: confirma que la DEC existe
    extras_tot = sorted(set(led["extras"]) | {e.replace("\\", "/").strip("/") for e in extras})
    rels = W.descubrir_miembros(raiz, lme, pq, extras_tot)
    man = W.manifiesto(raiz, rels)
    led.update({"emision": emision, "extras": extras_tot, "miembros": man})
    W.mover(raiz, led, "ENGINEERING", "FOR_REVIEW")
    led["estado"] = "FOR_REVIEW"
    led["ronda"] += 1
    led["fecha_envio"] = W.hoy()
    led.pop("fecha_auditoria", None)
    W.evento(raiz, led, "SEND_TO_REVIEW", "ENGINEERING", "FOR_REVIEW",
             f"ronda {led['ronda']}, {len(rels)} archivos" + (f", {permitir_varios}" if permitir_varios else ""))
    W.escribir_ledger(raiz, led)
    _estado_doc(raiz, lme, pq, "FOR_REVIEW")
    lme.guardar()
    print(f"{pq} → FOR_REVIEW (ronda {led['ronda']}, emisión {emision}, {len(rels)} archivos congelados).")
    print(f"Hoja de revisión requerida: 04_REVIEW/Review_Sheets/REVIEW-nn_{W.hoy().replace('-', '')}_{pq}.md "
          "con la línea «Resultado: APPROVED | APPROVED_WITH_COMMENTS | REJECTED | REJECTED_WITH_COMMENTS».")
    return led


def cli_send_to_review(argv=None):
    p = _parser("Mueve un paquete de 03_ENGINEERING a 04_REVIEW/Review_Packages y registra su manifiesto SHA-256.")
    p.add_argument("pq")
    p.add_argument("--emision", choices=W.EMISIONES)
    p.add_argument("--extra", action="append", default=[], help="ruta (relativa a 03_ENGINEERING) de un archivo o carpeta "
                   "adicional del paquete (p. ej. capítulos de un pliego); se recuerda en el registro")
    p.add_argument("--permitir-varios", metavar="DEC-nnn")
    a = p.parse_args(argv)
    send_to_review(_raiz(a), a.pq, a.emision, a.extra, a.permitir_varios)
    return 0


# --------------------------------------------------------------------------------- RETURN_TO_ENGINEERING
def return_to_engineering(raiz, pqs, motivo, con_dependientes=False, resultado=None):
    lme = W.LME(raiz)
    pqs = [W.validar_pq(q) for q in pqs]
    if not motivo or not motivo.strip():
        raise FwError("Indique el motivo (--motivo): queda en el historial del paquete.")
    if resultado and resultado not in W.RESULTADOS:
        raise FwError(f"Resultado inválido: {resultado}.")
    todos = W.todos_los_ledgers(raiz)
    if con_dependientes:
        cola = list(pqs)
        while cola:
            q = cola.pop()
            for otro in lme.paquetes():
                if q in lme.dependencias(otro) and otro in todos and otro not in pqs \
                        and todos[otro]["estado"] != "ENGINEERING":
                    pqs.append(otro)
                    cola.append(otro)
    avisos = []
    for pq in pqs:
        led = _led_o_error(raiz, pq)
        origen = led["estado"]
        if origen == "ENGINEERING":
            raise FwError(f"{pq} ya está en Ingeniería.")
        est, det = W.ubicaciones(raiz, led)
        if est != origen:
            raise FwError(f"{pq}: registro {origen} pero ubicación real {est} ({det}). Ejecute CHECK_STATE.py.")
        W.mover(raiz, led, origen, "ENGINEERING")
        led["estado"] = "ENGINEERING"
        W.evento(raiz, led, "RETURN_TO_ENGINEERING", origen, "ENGINEERING",
                 (f"[{resultado}] " if resultado else "") + motivo.strip())
        W.escribir_ledger(raiz, led)
        _estado_doc(raiz, lme, pq, "ENGINEERING")
        if origen in ("FOR_AUDIT", "RELEASED"):
            lme.poner(pq, "estado", "REABIERTO")
        print(f"{pq}: {origen} → ENGINEERING. Debe repetir el ciclo completo: revisión, auditoría, liberación.")
        # la auditoría de la emisión queda invalidada: los hermanos ya liberados y no emitidos vuelven a auditoría
        if origen in ("FOR_AUDIT", "RELEASED"):
            for q2, l2 in W.todos_los_ledgers(raiz).items():
                if q2 != pq and l2["estado"] == "RELEASED" and l2["emision"] == led["emision"] and q2 not in pqs \
                        and q2 in W.conjunto_pendiente(raiz, l2["emision"]):
                    W.mover(raiz, l2, "RELEASED", "FOR_AUDIT")
                    l2["estado"] = "FOR_AUDIT"
                    W.evento(raiz, l2, "AUDITORIA_INVALIDADA", "RELEASED", "FOR_AUDIT",
                             f"{pq} volvió a Ingeniería; la emisión {l2['emision']} debe re-auditarse")
                    W.escribir_ledger(raiz, l2)
                    _estado_doc(raiz, lme, q2, "FOR_AUDIT")
                    avisos.append(f"{q2}: RELEASED → FOR_AUDIT (la auditoría de {l2['emision']} quedó invalidada).")
        for otro in lme.paquetes():
            if pq in lme.dependencias(otro) and otro not in pqs:
                lo = W.leer_ledger(raiz, otro)
                if lo and lo["estado"] != "ENGINEERING":
                    avisos.append(f"{otro} depende de {pq} y está en {lo['estado']}: si usa un dato modificado debe volver "
                                  f"a Ingeniería (RETURN_TO_ENGINEERING.py {otro}), o repita con --con-dependientes.")
    lme.guardar()
    W.nota_changelog(raiz, f"{', '.join(pqs)} vuelven a Ingeniería: {motivo.strip()}")
    for a in avisos:
        print("AVISO:", a)
    return pqs, avisos


def cli_return_to_engineering(argv=None):
    p = _parser("Devuelve uno o más paquetes a 03_ENGINEERING (el ciclo se reinicia por completo).")
    p.add_argument("pq", nargs="+")
    p.add_argument("--motivo", required=True)
    p.add_argument("--resultado", choices=W.RESULTADOS)
    p.add_argument("--con-dependientes", action="store_true")
    a = p.parse_args(argv)
    return_to_engineering(_raiz(a), a.pq, a.motivo, a.con_dependientes, a.resultado)
    return 0


# --------------------------------------------------------------------------------- SEND_TO_AUDIT
def estado_conjunto(raiz, lme, emision):
    pend = W.conjunto_pendiente(raiz, emision)
    faltan = W.paquetes_faltantes(raiz, lme, emision)
    led = W.todos_los_ledgers(raiz)
    fuera = [q for q in pend if led[q]["estado"] != "FOR_AUDIT"]
    return pend, sorted(set(faltan + fuera))


def send_to_audit(raiz, pq, solo_documental=None):
    pq = W.validar_pq(pq)
    lme = W.LME(raiz)
    led = _led_o_error(raiz, pq)
    _verificar_ubicacion(raiz, led, "FOR_REVIEW")
    h = W.hoja_vigente(raiz, pq)
    if not h:
        raise FwError(f"{pq}: no hay hoja de revisión (04_REVIEW/Review_Sheets/REVIEW-nn_YYYYMMDD_{pq}.md).")
    ruta, res, fecha = h
    if fecha and led["fecha_envio"] and fecha < led["fecha_envio"]:
        raise FwError(f"{pq}: la hoja vigente ({os.path.basename(ruta)}) es anterior al último envío a revisión "
                      f"({led['fecha_envio']}); falta la hoja de esta ronda.")
    if res != "APPROVED":
        if res == "APPROVED_WITH_COMMENTS" and solo_documental:  # A2: comentarios solo documentales
            W.validar_dec_existe(raiz, solo_documental)
        else:
            accion = ("falta el campo «Resultado:» en la hoja" if res is None else
                      f"el resultado es {res}: solo APPROVED avanza (o APPROVED_WITH_COMMENTS con DEC registrada "
                      f"--solo-documental DEC-nnn); ejecute RETURN_TO_ENGINEERING.py {pq} --resultado {res}")
            raise FwError(f"{pq} no puede pasar a auditoría: {accion}.")
    W.mover(raiz, led, "FOR_REVIEW", "FOR_AUDIT")
    led["estado"] = "FOR_AUDIT"
    led["fecha_auditoria"] = W.hoy()
    W.evento(raiz, led, "SEND_TO_AUDIT", "FOR_REVIEW", "FOR_AUDIT", f"hoja {os.path.basename(ruta)}: APPROVED")
    W.escribir_ledger(raiz, led)
    _estado_doc(raiz, lme, pq, "FOR_AUDIT")
    lme.guardar()
    print(f"{pq} → FOR_AUDIT.")
    pend, faltan = estado_conjunto(raiz, lme, led["emision"])
    if faltan:
        print(f"Conjunto {led['emision']}: faltan en auditoría {', '.join(faltan)}. La auditoría se hace una sola vez, "
              "con todo el conjunto.")
    else:
        print(f"Conjunto {led['emision']} completo en auditoría ({', '.join(pend)}): puede iniciarse la auditoría de la emisión.")
    return led


def cli_send_to_audit(argv=None):
    p = _parser("Mueve un paquete con revisión APPROVED (o APPROVED_WITH_COMMENTS con DEC) de 04_REVIEW a 05_AUDIT/Audit_Packages.")
    p.add_argument("pq")
    p.add_argument("--solo-documental", metavar="DEC-nnn",
                   help="permite avanzar con APPROVED_WITH_COMMENTS si los comentarios son solo documentales (requiere DEC registrada)")
    a = p.parse_args(argv)
    send_to_audit(_raiz(a), a.pq, a.solo_documental)
    return 0


# --------------------------------------------------------------------------------- APPROVE_AUDIT
def approve_audit(raiz, emision, aud=None):
    emision = emision.upper()
    W.exigir_fase(raiz, emision)
    lme = W.LME(raiz)
    pend, faltan = estado_conjunto(raiz, lme, emision)
    if not pend:
        raise FwError(f"No hay paquetes de la emisión {emision} pendientes de auditoría.")
    if faltan:
        raise FwError(f"El conjunto {emision} no está completo en 05_AUDIT: faltan {', '.join(faltan)}.")
    ledgers = W.todos_los_ledgers(raiz)
    for q in pend:
        _verificar_ubicacion(raiz, ledgers[q], "FOR_AUDIT")
    informes = [i for i in W.informes_auditoria(raiz) if i["emision"] == emision and (not aud or i["id"] == aud)]
    if not informes:
        raise FwError(f"No hay informe de auditoría de la emisión {emision} (05_AUDIT/Audit_Reports/AUD-nn_YYYYMMDD.md "
                      "con «Emisión:», «Paquetes:» y «Resultado:»).")
    inf = informes[-1]
    if inf["resultado"] != "APPROVED":
        raise FwError(f"{inf['id']}: Resultado {inf['resultado']}. Solo APPROVED avanza; devuelva a Ingeniería los paquetes con "
                      "hallazgos (RETURN_TO_ENGINEERING.py) y repita la auditoría del conjunto.")
    if sorted(inf["paquetes"]) != sorted(pend):
        raise FwError(f"{inf['id']} audita {', '.join(inf['paquetes']) or '(sin «Paquetes:»)'} pero el conjunto es "
                      f"{', '.join(sorted(pend))}.")
    ult = max(ledgers[q].get("fecha_auditoria") or "" for q in pend)
    if inf["fecha"] and ult and inf["fecha"] < ult:
        raise FwError(f"{inf['id']} ({inf['fecha']}) es anterior al ingreso del último paquete a auditoría ({ult}).")
    for q in pend:
        led = ledgers[q]
        W.mover(raiz, led, "FOR_AUDIT", "RELEASED")
        led["estado"] = "RELEASED"
        led["auditoria"] = {"id": inf["id"], "fecha": W.hoy(), "emision": emision}
        W.evento(raiz, led, "APPROVE_AUDIT", "FOR_AUDIT", "RELEASED", f"{inf['id']} APPROVED")
        W.escribir_ledger(raiz, led)
        _estado_doc(raiz, lme, q, "RELEASED")
        lme.poner(q, "auditado", inf["id"])
    lme.guardar()
    W.nota_changelog(raiz, f"Auditoría {inf['id']} aprobada: {emision} ({', '.join(sorted(pend))}) → 06_RELEASED")
    print(f"{inf['id']} APPROVED: {', '.join(sorted(pend))} → RELEASED.")
    return inf


def cli_approve_audit(argv=None):
    p = _parser("Con el informe de auditoría APPROVED, mueve el conjunto de la emisión de 05_AUDIT a 06_RELEASED.")
    p.add_argument("--emision", required=True, choices=W.EMISIONES)
    p.add_argument("--aud", metavar="AUD-nn")
    a = p.parse_args(argv)
    approve_audit(_raiz(a), a.emision, a.aud)
    return 0


# --------------------------------------------------------------------------------- RELEASE_DOCUMENTS
def release_documents(raiz, emision):
    emision = emision.upper()
    W.exigir_fase(raiz, emision)
    lme = W.LME(raiz)
    pend = W.conjunto_pendiente(raiz, emision)
    if not pend:
        raise FwError(f"No hay paquetes de {emision} pendientes de emitir.")
    ledgers = W.todos_los_ledgers(raiz)
    faltan = [q for q in pend if ledgers[q]["estado"] != "RELEASED"]
    faltan += W.paquetes_faltantes(raiz, lme, emision)
    if faltan:
        raise FwError(f"El conjunto {emision} no está completo en 06_RELEASED: {', '.join(sorted(set(faltan)))}.")
    reg = {"emision": emision, "fecha": W.hoy(), "paquetes": {}}
    for q in sorted(pend):
        _verificar_ubicacion(raiz, ledgers[q], "RELEASED")
        reg["paquetes"][q] = {"ronda": ledgers[q]["ronda"], "auditoria": ledgers[q].get("auditoria", {}).get("id"),
                              "archivos": {r: m["sha256"] for r, m in ledgers[q]["miembros"].items()}}
    with open(os.path.join(raiz, W.DIR_REL, f"RELEASE_{emision}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    lineas = [f"# RELEASE_{emision} — conjunto liberado para emitir", "",
              f"Fecha: {reg['fecha']} · Generado por RELEASE_DOCUMENTS.py (no se edita).", "",
              "| Paquete | Auditoría | Archivos |", "|---|---|---|"]
    for q, d in reg["paquetes"].items():
        lineas.append(f"| {q} | {d['auditoria']} | {len(d['archivos'])} |")
    lineas += ["", "Antes de emitir: el usuario depura DWG y PDF (lista DE-01 a DE-10, `FOLDER_TEMPLATES.md`, 4.5) y solo entran "
               "los planos `REVIEWED` en `DRAWING_STATUS.md`. Luego `ISSUE_" + ("ASBUILT" if emision == "AS_BUILT" else emision) + ".py`."]
    with open(os.path.join(raiz, W.DIR_REL, f"RELEASE_{emision}.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    print(f"Liberado {emision}: {', '.join(sorted(pend))} (06_RELEASED/RELEASE_{emision}.md).")
    return reg


def cli_release_documents(argv=None):
    p = _parser("Verifica el conjunto de 06_RELEASED y deja el registro de liberación de la emisión.")
    p.add_argument("--emision", required=True, choices=W.EMISIONES)
    a = p.parse_args(argv)
    release_documents(_raiz(a), a.emision)
    return 0


# --------------------------------------------------------------------------------- ISSUE_*
def _destino_emision(rel):
    b = os.path.basename(rel)
    bl = b.lower()
    if "_DIN_" in b:
        return None                                   # insumo interno de dibujo: no se emite
    if bl.endswith((".dwg", ".dxf")) or "xref" in bl:
        return "Drawings_DWG"
    if bl.endswith(".pdf") and re.search(r"-(PL|DG)-\d{3}", b):
        return "Drawings_PDF"
    return "Documents"


def issue(raiz, emision, tr=None):
    emision = emision.upper()
    W.exigir_fase(raiz, emision)
    rev = "01" if emision == "AS_BUILT" else "00"
    regp = os.path.join(raiz, W.DIR_REL, f"RELEASE_{emision}.json")
    if not os.path.exists(regp):
        raise FwError(f"Falta 06_RELEASED/RELEASE_{emision}.json: ejecute RELEASE_DOCUMENTS.py --emision {emision}.")
    with open(regp, encoding="utf-8") as f:
        reg = json.load(f)
    ledgers = W.todos_los_ledgers(raiz)
    lme = W.LME(raiz)
    for q, d in reg["paquetes"].items():
        led = ledgers.get(q)
        if led is None or led["ronda"] != d["ronda"]:
            raise FwError(f"{q}: cambió desde la liberación (ronda distinta). Repita RELEASE_DOCUMENTS.py.")
        _verificar_ubicacion(raiz, led, "RELEASED")
    tr = tr or W.siguiente_tr(raiz)
    if not re.fullmatch(r"TR-\d{3}", tr):
        raise FwError(f"Transmittal inválido: {tr} (formato TR-nnn).")
    fecha = W.hoy()
    carpeta = f"{fecha.replace('-', '')}_{tr}_Rev{rev}"
    base = os.path.join(raiz, W.DIR_ENT, W.CARPETA_EMISION[emision], carpeta)
    if os.path.exists(base):
        raise FwError(f"Ya existe {os.path.relpath(base, raiz)}.")
    copiados, omitidos, rotular, destinos = [], [], [], {}
    for q, d in sorted(reg["paquetes"].items()):
        for rel in sorted(d["archivos"]):
            sub = _destino_emision(rel)
            if sub is None:
                omitidos.append(rel)
                continue
            nombre = W.RE_REV_NOMBRE.sub(f"_Rev{rev}", os.path.basename(rel), count=1)
            dest = f"{sub}/{nombre}"
            if dest in destinos:
                raise FwError(f"Colisión de nombres en la emisión: {dest} ({destinos[dest]} y {q}/{rel}).")
            destinos[dest] = f"{q}/{rel}"
            origen = os.path.join(raiz, W.DIR_REL, q, rel)
            os.makedirs(os.path.join(base, sub), exist_ok=True)
            shutil.copy2(origen, os.path.join(base, dest))
            copiados.append((q, rel, dest, W.sha256(os.path.join(base, dest))))
            if nombre.lower().endswith(".md"):
                rotular.append(dest)
    tl = [f"# {tr} — Transmittal (borrador)", "", f"Emisión: {emision} · Rótulo al cliente: Rev {rev} · Fecha: {fecha}", "",
          "| Paquete | Archivo emitido | Archivo de trabajo (revisión interna) | SHA-256 (12) |", "|---|---|---|---|"]
    for q, rel, dest, h in copiados:
        tl.append(f"| {q} | {dest} | {os.path.basename(rel)} | {h[:12]} |")
    if omitidos:
        tl += ["", "No emitidos (internos): " + ", ".join(os.path.basename(o) for o in omitidos)]
    tl += ["", "Pendiente antes de enviar (lo hace Claude/usuario, `FOLDER_TEMPLATES.md`, 4.5): rotular portadas y referencias de los "
           "`.md` en Rev " + rev + ", exportar los documentos al formato final, depurar DWG/PDF (DE-01 a DE-10). "
           "Con `entrega enviada " + tr + "` se confirma el envío (CONFIRM_SENT.py)."]
    tp = os.path.join(raiz, W.DIR_ENT, "TRANSMITTALS", f"{tr}.md")
    os.makedirs(os.path.dirname(tp), exist_ok=True)
    texto = "\n".join(tl) + "\n"
    for destp in (tp, os.path.join(base, f"{tr}.md")):
        with open(destp, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    for q, d in reg["paquetes"].items():
        led = ledgers[q]
        mios = {dest: h for qq, rel, dest, h in copiados if qq == q}
        led["emitido"].append({"emision": emision, "tr": tr, "fecha": fecha, "ronda": led["ronda"], "carpeta": carpeta,
                               "confirmado": False, "archivos": mios})
        W.evento(raiz, led, f"ISSUE_{emision}", "RELEASED", "RELEASED", f"{tr} (borrador) en 07_DELIVERABLES/{emision}/{carpeta}")
        W.escribir_ledger(raiz, led)
        lme.poner(q, "entrega", f"{tr} (borrador) Rev {rev}")
    lme.guardar()
    os.replace(regp, os.path.join(raiz, W.DIR_REL, f"RELEASE_{emision}_{tr}.json"))
    os.replace(regp[:-5] + ".md", os.path.join(raiz, W.DIR_REL, f"RELEASE_{emision}_{tr}.md"))
    W.nota_changelog(raiz, f"{emision} {tr}: emisión preparada en 07_DELIVERABLES/{emision}/{carpeta}")
    print(f"{emision} {tr}: {len(copiados)} archivos copiados a 07_DELIVERABLES/{emision}/{carpeta}.")
    if rotular:
        print("Pendiente: rotular portada/referencias (Rev " + rev + ") en: " + ", ".join(rotular))
    return tr, carpeta


def _cli_issue(emision, argv):
    p = _parser(f"Copia el conjunto liberado ({emision}) a 07_DELIVERABLES con nombres Rev rotulados y transmittal borrador.")
    p.add_argument("--tr", metavar="TR-nnn")
    a = p.parse_args(argv)
    issue(_raiz(a), emision, a.tr)
    return 0


def cli_issue_ifa(argv=None):
    return _cli_issue("IFA", argv)


def cli_issue_ifc(argv=None):
    return _cli_issue("IFC", argv)


def cli_issue_asbuilt(argv=None):
    return _cli_issue("AS_BUILT", argv)


# --------------------------------------------------------------------------------- CONFIRM_SENT
def confirm_sent(raiz, tr):
    lme = W.LME(raiz)
    n = 0
    for pq, led in W.todos_los_ledgers(raiz).items():
        for e in led["emitido"]:
            if e["tr"] == tr:
                if e["confirmado"]:
                    raise FwError(f"{tr} ya estaba confirmado.")
                e["confirmado"] = True
                W.evento(raiz, led, "CONFIRM_SENT", "RELEASED", "RELEASED", f"{tr} enviado al cliente ({e['emision']})")
                W.escribir_ledger(raiz, led)
                lme.poner(pq, "estado", e["emision"])
                rev = "01" if e["emision"] == "AS_BUILT" else "00"
                lme.poner(pq, "entrega", f"{tr} Rev {rev}")
                n += 1
    if not n:
        raise FwError(f"No hay emisión {tr}.")
    lme.guardar()
    W.nota_changelog(raiz, f"{tr} enviado al cliente")
    print(f"{tr} confirmado ({n} paquetes).")
    return n


def cli_confirm_sent(argv=None):
    p = _parser("Registra que el transmittal fue enviado al cliente (el estado documental pasa a IFA / IFC / AS_BUILT).")
    p.add_argument("tr")
    a = p.parse_args(argv)
    confirm_sent(_raiz(a), a.tr)
    return 0


# --------------------------------------------------------------------------------- START_ASBUILT
def start_asbuilt(raiz):
    W.exigir_fase(raiz, "AS_BUILT")
    lme = W.LME(raiz)
    movidos = []
    for pq, led in W.todos_los_ledgers(raiz).items():
        if not any(e["emision"] == "IFC" and e["confirmado"] and e["ronda"] == led["ronda"] for e in led["emitido"]):
            continue
        if led["estado"] != "RELEASED":
            raise FwError(f"{pq} tiene IFC emitido pero está en {led['estado']}: resuelva ese estado antes de iniciar el as-built.")
        _verificar_ubicacion(raiz, led, "RELEASED")
        W.mover(raiz, led, "RELEASED", "ENGINEERING")
        led.update({"estado": "ENGINEERING", "emision": "AS_BUILT", "fase": "ASB"})
        W.evento(raiz, led, "START_ASBUILT", "RELEASED", "ENGINEERING", "documentación conforme a obra (fase ASB)")
        W.escribir_ledger(raiz, led)
        lme.poner(pq, "estado", "DRAFT")
        movidos.append(pq)
    if not movidos:
        raise FwError("No hay paquetes con IFC emitido y confirmado (CONFIRM_SENT.py).")
    lme.guardar()
    W.nota_changelog(raiz, f"As-built iniciado: {', '.join(movidos)} vuelven a Ingeniería (fase ASB)")
    print(f"As-built: {', '.join(movidos)} → ENGINEERING (emisión AS_BUILT, Rev 01 al emitir).")
    return movidos


def cli_start_asbuilt(argv=None):
    p = _parser("Devuelve a Ingeniería los paquetes emitidos en IFC para elaborar la documentación as-built.")
    a = p.parse_args(argv)
    start_asbuilt(_raiz(a))
    return 0


# --------------------------------------------------------------------------------- CLOSE_PROJECT
def _emision_de_cierre(raiz, sin_asbuilt):
    """(emisión que debe estar confirmada para cerrar, decisión por la que no hay as-built): la de la fase final del proyecto, o IFC si se cierra sin as-built por una decisión registrada."""
    fin = W.fase_final(raiz)
    if fin is None:
        return ("IFC" if sin_asbuilt else "AS_BUILT"), sin_asbuilt
    return W.EMISION_FINAL[fin], sin_asbuilt or (f"el proyecto termina en la fase {fin}" if fin != "ASB" else None)


def _sin_emision(led, req):
    """Si al paquete le falta la emisión final confirmada en su ronda (sin emisión de cierre, no le falta nada)."""
    return bool(req) and not any(e["emision"] == req and e["confirmado"] and e["ronda"] == led["ronda"] for e in led["emitido"])


def close_project(raiz, sin_asbuilt=None):
    lme = W.LME(raiz)
    ledgers = W.todos_los_ledgers(raiz)
    falt = [q for q in lme.paquetes() if q not in ledgers]
    if falt:
        raise FwError(f"Paquetes sin registro de flujo (nunca enviados): {', '.join(falt)}.")
    req, sin_asbuilt = _emision_de_cierre(raiz, sin_asbuilt)
    mal = []
    for pq, led in ledgers.items():
        if led["estado"] != "RELEASED":
            mal.append(f"{pq} está en {led['estado']}")
        elif _sin_emision(led, req):
            mal.append(f"{pq} sin {req} emitido y confirmado")
        else:
            dif = W.hash_ok(raiz, led, "RELEASED")
            if dif:
                mal.append(f"{pq} modificado")
    if mal:
        raise FwError("No se puede cerrar: " + "; ".join(mal) + ".")
    for pq in ledgers:
        lme.poner(pq, "estado", "CLOSED")
        led = ledgers[pq]
        W.evento(raiz, led, "CLOSE_PROJECT", "RELEASED", "RELEASED", sin_asbuilt or "as-built entregado")
        W.escribir_ledger(raiz, led)
    lme.guardar()
    cuerpo = ["# CIERRE DEL PROYECTO", "", f"Fecha: {W.hoy()} · Generado por CLOSE_PROJECT.py", "",
              f"Emisión final: {req or '—'}" + (f" (sin as-built, {sin_asbuilt})" if sin_asbuilt else ""), "",
              "| Paquete | Rondas | Emisiones |", "|---|---|---|"]
    for pq, led in sorted(ledgers.items()):
        cuerpo.append(f"| {pq} | {led['ronda']} | " + ", ".join(f"{e['emision']} {e['tr']}" for e in led["emitido"]) + " |")
    with open(os.path.join(raiz, W.DIR_LED, "CLOSURE.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(cuerpo) + "\n")
    W.nota_changelog(raiz, "Proyecto CERRADO")
    print("Proyecto CLOSED. Registro en 90_MANAGEMENT/LEDGER/CLOSURE.md.")


def cli_close_project(argv=None):
    p = _parser("Cierra el proyecto si todos los paquetes tienen su emisión final confirmada y están intactos.")
    p.add_argument("--sin-asbuilt", metavar="DEC-nnn", help="proyecto sin as-built contratado (decisión registrada)")
    a = p.parse_args(argv)
    close_project(_raiz(a), a.sin_asbuilt)
    return 0


# --------------------------------------------------------------------------------- CHECK_STATE
SIGUIENTE = {
    "ENGINEERING": "desarrollar y, con autocontrol hecho, SEND_TO_REVIEW.py",
    "FOR_REVIEW": "el usuario revisa y completa «Resultado:» en la hoja; si APPROVED → SEND_TO_AUDIT.py; si no → RETURN_TO_ENGINEERING.py",
    "FOR_AUDIT": "auditar el conjunto de la emisión; informe con «Resultado:»; si APPROVED → APPROVE_AUDIT.py",
    "RELEASED": "RELEASE_DOCUMENTS.py → ISSUE_*.py → CONFIRM_SENT.py",
}


def check_state(raiz, escribir=False):
    lme = W.LME(raiz)
    ledgers = W.todos_los_ledgers(raiz)
    errores, avisos, filas = [], [], []
    for pq in sorted(set(lme.paquetes()) | set(ledgers)):
        led = ledgers.get(pq)
        if led is None:
            filas.append((pq, "ENGINEERING", "sin enviar", "—", "desarrollar y SEND_TO_REVIEW.py"))
            continue
        est, det = W.ubicaciones(raiz, led) if led["miembros"] else (led["estado"], "")
        if est != led["estado"]:
            errores.append(f"{pq}: registro {led['estado']} ≠ ubicación real {est} ({det}).")
        elif det:
            errores.append(f"{pq}: {det}.")
        nota = ""
        if led["estado"] != "ENGINEERING" and est == led["estado"]:
            dif = W.hash_ok(raiz, led, est)
            if dif:
                errores.append(f"{pq}: MODIFICADO en {led['estado']} ({'; '.join(dif[:3])}) → RETURN_TO_ENGINEERING.py {pq}.")
                nota = "MODIFICADO"
            # copias sueltas en Ingeniería
            eng = [r for r in led["miembros"] if os.path.isfile(os.path.join(raiz, W.DIR_ING, r))]
            if eng:
                errores.append(f"{pq}: {len(eng)} archivo(s) del paquete también existen en 03_ENGINEERING (duplicado/edición fuera de flujo).")
        for e in led["emitido"]:
            for dest, h in e["archivos"].items():
                p = os.path.join(raiz, W.DIR_ENT, W.CARPETA_EMISION[e["emision"]], e["carpeta"], dest)
                if not os.path.isfile(p):
                    errores.append(f"{pq}: falta en 07_DELIVERABLES {dest} ({e['tr']}).")
                elif W.sha256(p) != h and e.get("confirmado"):
                    avisos.append(f"{pq}: {dest} ({e['tr']}) difiere de lo emitido; si es el rotulado de portada, registre la huella.")
        if led["estado"] == "FOR_REVIEW":
            h = W.hoja_vigente(raiz, pq)
            if not h:
                nota = nota or "falta la hoja de revisión"
            else:
                nota = nota or f"hoja {os.path.basename(h[0])}: {h[1] or 'sin Resultado'}"
        filas.append((pq, led["estado"], nota or f"ronda {led['ronda']}", led["emision"] or "—",
                      SIGUIENTE.get(led["estado"], "")))
        if led["estado"] != "ENGINEERING":
            for dep in lme.dependencias(pq):
                d = ledgers.get(dep)
                if d is None or d["estado"] == "ENGINEERING":
                    avisos.append(f"{pq} ({led['estado']}) depende de {dep}, que está en Ingeniería: revalidar si usa un dato modificado.")
    conj = []
    for em in W.EMISIONES:
        pend = W.conjunto_pendiente(raiz, em)
        if pend:
            pend, faltan = estado_conjunto(raiz, lme, em)
            conj.append((em, W.conjunto_pendiente(raiz, em), faltan))
    estados = [f[1] for f in filas]
    derivado = ("ENGINEERING" if "ENGINEERING" in estados else "FOR_REVIEW" if "FOR_REVIEW" in estados else
                "FOR_AUDIT" if "FOR_AUDIT" in estados else "RELEASED" if estados else "PLANNING")
    fase, emision_activa, proxima_puerta = W.fase_limitada(ledgers, raiz)
    avisos_ver = W.verificar_version()  # M7: alerta de drift de versión
    out = ["# ESTADO CALCULADO (vista derivada de la ubicación de los paquetes)", "",
           f"Fecha: {W.hoy()} · Generado por CHECK_STATE.py; no se edita.", "",
           f"**Fase:** {fase}  ·  **Emisión activa:** {emision_activa or '—'}  ·  **Próxima puerta:** {proxima_puerta}", "",
           f"Estado documental derivado: **{derivado}** (los estados de obra —CONSTRUCTION…— los declara el usuario en `PROJECT_STATUS.md`).", "",
           "| Paquete | Ubicación / estado | Detalle | Emisión | Siguiente paso |", "|---|---|---|---|---|"]
    out += [f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in filas]
    for em, pend, faltan in conj:
        out.append("")
        out.append(f"Conjunto {em}: {', '.join(pend)} — " + ("COMPLETO en auditoría o liberado" if not faltan else
                   f"incompleto, falta: {', '.join(faltan)}"))
    if errores:
        out += ["", "## Errores"] + [f"- {e}" for e in errores]
    if avisos:
        out += ["", "## Avisos"] + [f"- {a}" for a in avisos]
    if avisos_ver:
        out += ["", "## Versión"] + [f"- {a}" for a in avisos_ver]
    texto = "\n".join(out) + "\n"
    print(texto)
    if escribir:
        os.makedirs(os.path.join(raiz, W.DIR_LED), exist_ok=True)
        with open(os.path.join(raiz, W.DIR_LED, "COMPUTED_STATE.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    return errores, avisos, filas, derivado


def cli_check_state(argv=None):
    p = _parser("Verifica que la ubicación, el manifiesto y las emisiones sean coherentes; muestra el siguiente paso de cada paquete.")
    p.add_argument("--escribir", action="store_true", help="guarda la vista en 90_MANAGEMENT/LEDGER/COMPUTED_STATE.md")
    p.add_argument("--actualizar-states", action="store_true", help="regenera states.json con la versión actual del motor (M7)")
    a = p.parse_args(argv)
    if a.actualizar_states:
        W.escribir_states()
        print(f"states.json actualizado a versión {W.__version__}.")
    errores = check_state(_raiz(a), a.escribir)[0]
    return 1 if errores else 0

# --------------------------------------------------------------------------------- SYNC_CCPM (M2)
def sync_ccpm(raiz, ccpm_input=None):
    """Lee los LEDGER/PQ-nn.json y actualiza inicio_real/fin_real en ccpm_input.json (M2)."""
    import glob
    ccpm_input = ccpm_input or os.path.join(raiz, "90_MANAGEMENT", "Planning", "ccpm_input.json")
    if not os.path.exists(ccpm_input):
        raise FwError(f"No se encontró {ccpm_input}. Cree el archivo ccpm_input.json primero.")
    with open(ccpm_input, encoding="utf-8") as f:
        data = json.load(f)
    ledgers = W.todos_los_ledgers(raiz)
    actualizados = 0
    for tarea in data.get("tareas", []):
        pq = tarea.get("paquete")
        fase = tarea.get("fase_paquete")
        if not pq or not fase:
            continue
        led = ledgers.get(pq)
        if led is None:
            continue
        # fase "elaborar": inicio = primer envío a FOR_REVIEW, fin = mismo día
        # fase "revisar": inicio = fecha_envio a FOR_REVIEW, fin = hoja vigente
        # fase "procesar": N/A (depende del usuario)
        eventos = {e["evento"]: e["fecha"] for e in led.get("historial", [])}
        if fase == "elaborar" and led.get("fecha_envio"):
            tarea.setdefault("inicio_real", led["fecha_envio"])
            if led["estado"] != "ENGINEERING":
                tarea["estado"] = "hecha"
                tarea["fin_real"] = led["fecha_envio"]
                actualizados += 1
        elif fase == "revisar" and led.get("fecha_envio"):
            tarea["inicio_real"] = led["fecha_envio"]
            h = W.hoja_vigente(raiz, pq)
            if h and h[1] in ("APPROVED", "APPROVED_WITH_COMMENTS"):
                tarea["estado"] = "hecha"
                tarea["fin_real"] = h[2] or led["fecha_envio"]
                actualizados += 1
    with open(ccpm_input, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    print(f"sync_ccpm: {actualizados} tareas actualizadas en {os.path.relpath(ccpm_input, raiz)}.")
    return actualizados


def cli_sync_ccpm(argv=None):
    p = _parser("Actualiza inicio_real/fin_real en ccpm_input.json desde los LEDGER del proyecto (M2).")
    p.add_argument("--ccpm-input", metavar="RUTA", help="ruta al ccpm_input.json (por defecto 90_MANAGEMENT/Planning/ccpm_input.json)")
    a = p.parse_args(argv)
    sync_ccpm(_raiz(a), a.ccpm_input)
    return 0


# --------------------------------------------------------------------------------- PROGRESS_REPORT (M3)
def progress_report(raiz, salida=None):
    """Genera un borrador de reporte de avance en Markdown desde LEDGER + LME (M3)."""
    lme = W.LME(raiz)
    ledgers = W.todos_los_ledgers(raiz)
    hoy = W.hoy()
    fase, emision_activa, proxima_puerta = W.fase_limitada(ledgers, raiz)
    paquetes = sorted(set(lme.paquetes()) | set(ledgers))
    filas = []
    en_ing = en_rev = en_aud = liberados = 0
    for pq in paquetes:
        led = ledgers.get(pq)
        estado = led["estado"] if led else "ENGINEERING"
        emision = (led["emision"] or "—") if led else "—"
        ronda = led["ronda"] if led else 0
        emitidas = [e["emision"] for e in led.get("emitido", []) if e.get("confirmado")] if led else []
        filas.append((pq, estado, emision, ronda, ", ".join(emitidas) or "—"))
        if estado == "ENGINEERING": en_ing += 1
        elif estado == "FOR_REVIEW": en_rev += 1
        elif estado == "FOR_AUDIT": en_aud += 1
        elif estado == "RELEASED": liberados += 1
    total = len(paquetes) or 1
    pct = round(liberados / total * 100)
    lineas = [
        "# REPORTE DE AVANCE — BORRADOR",
        "",
        f"> Generado por PROGRESS_REPORT.py · {hoy} · *Completar secciones marcadas con TODO.*",
        "",
        "## A. Estado general",
        "",
        f"| Indicador | Valor |",
        "|---|---|",
        f"| Fecha de corte | {hoy} |",
        f"| Fase PM² | {fase} |",
        f"| Emisión activa | {emision_activa or '—'} |",
        f"| Próxima puerta | {proxima_puerta} |",
        f"| Paquetes totales | {total} |",
        f"| En Ingeniería | {en_ing} |",
        f"| En Revisión | {en_rev} |",
        f"| En Auditoría | {en_aud} |",
        f"| Liberados | {liberados} |",
        f"| % completado (RELEASED/total) | {pct} % |",
        "",
        "## B. Paquetes de revisión",
        "",
        "| Paquete | Estado | Emisión | Ronda | Emitido confirmado |",
        "|---|---|---|---|---|",
    ]
    for pq, est, em, rnd, emit in filas:
        lineas.append(f"| {pq} | {est} | {em} | {rnd} | {emit} |")
    lineas += [
        "",
        "## C. Incidencias abiertas",
        "",
        "> TODO: copiar las incidencias ABIERTO / EN CURSO de `ISSUE_LOG.md`.",
        "",
        "## D. Riesgos activos",
        "",
        "> TODO: copiar los RIE-nnn activos de `ASSUMPTIONS_AND_DECISIONS.md`.",
        "",
        "## E. Próximas acciones",
        "",
        "> TODO: completar con el plan de la próxima semana / sprint.",
        "",
    ]
    texto = "\n".join(lineas) + "\n"
    if salida:
        with open(salida, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print(f"Reporte escrito en {salida}.")
    else:
        print(texto)
    return texto


def cli_progress_report(argv=None):
    p = _parser("Genera un borrador de reporte de avance en Markdown (M3).")
    p.add_argument("--salida", metavar="RUTA.md", help="escribe en archivo en lugar de stdout")
    a = p.parse_args(argv)
    progress_report(_raiz(a), a.salida)
    return 0


# --------------------------------------------------------------------------------- EFFORT_REPORT (G3)
def _parse_effort_table(raiz):
    """Lee la tabla de EFFORT_BASELINE.md. Devuelve lista de dicts."""
    p = os.path.join(raiz, W.DIR_GES, "Planning", "EFFORT_BASELINE.md")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        lineas = f.read().splitlines()
    header = None
    cols = {}
    rows = []
    for i, l in enumerate(lineas):
        t = l.strip()
        if not t.startswith("|"):
            continue
        celdas = [c.strip() for c in t.strip("|").split("|")]
        if header is None:
            nl = [c.lower() for c in celdas]
            if any("paquete" in c for c in nl):
                header = i
                for j, c in enumerate(nl):
                    if "paquete" in c: cols["paquete"] = j
                    elif "estimada" in c: cols["estimada"] = j
                    elif "real" in c: cols["real"] = j
                    elif "avance" in c or "%" in c: cols["pct"] = j
                    elif "disciplina" in c: cols["disciplina"] = j
        elif i == header + 1:
            continue  # separator row
        else:
            if not any(c for c in celdas):
                break
            row = {k: (celdas[v] if v < len(celdas) else "") for k, v in cols.items()}
            if row.get("paquete"):
                rows.append(row)
    return rows


def effort_report(raiz, salida=None):
    """Compara horas estimadas vs reales en EFFORT_BASELINE.md (G3)."""
    rows = _parse_effort_table(raiz)
    if not rows:
        raise FwError("EFFORT_BASELINE.md no tiene tabla de esfuerzo o está vacía.")
    def _h(s):
        try: return float(str(s).replace("h", "").replace(",", ".").strip() or 0)
        except: return 0.0
    total_est = total_real = total_gan = 0.0
    lineas = [
        "# REPORTE DE ESFUERZO — " + W.hoy(),
        "",
        "| Paquete | Estimada h | Real h | % Avance | Ganadas h | Desvío h |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        est = _h(r.get("estimada"))
        real = _h(r.get("real"))
        pct = _h(r.get("pct"))
        gan = est * pct / 100 if pct else 0
        desv = real - gan
        total_est += est; total_real += real; total_gan += gan
        lineas.append(f"| {r.get('paquete','')} | {est:.0f} | {real:.0f} | {pct:.0f}% | {gan:.0f} | {desv:+.0f} |")
    total_desv = total_real - total_gan
    lineas += [
        f"| **TOTAL** | **{total_est:.0f}** | **{total_real:.0f}** | — | **{total_gan:.0f}** | **{total_desv:+.0f}** |",
        "",
        f"SPI (esfuerzo ganado / real) = **{total_gan/total_real:.2f}**" if total_real else "",
    ]
    texto = "\n".join(l for l in lineas) + "\n"
    if salida:
        with open(salida, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print(f"Reporte escrito en {salida}.")
    else:
        print(texto)
    return texto


def cli_effort_report(argv=None):
    p = _parser("Compara horas estimadas vs reales en EFFORT_BASELINE.md y calcula SPI de esfuerzo (G3).")
    p.add_argument("--salida", metavar="RUTA.md")
    a = p.parse_args(argv)
    effort_report(_raiz(a), a.salida)
    return 0


# --------------------------------------------------------------------------------- CHECK_INF (G5)
def check_inf(raiz):
    """Lista incidencias tipo INF vencidas o próximas a vencer en ISSUE_LOG.md (G5)."""
    p = os.path.join(raiz, W.DIR_GES, "ISSUE_LOG.md")
    if not os.path.exists(p):
        raise FwError("No existe 90_MANAGEMENT/ISSUE_LOG.md.")
    with open(p, encoding="utf-8") as f:
        lineas = f.read().splitlines()
    hoy = W.hoy()
    header = None
    cols = {}
    vencidas = proximas = []
    for i, l in enumerate(lineas):
        t = l.strip()
        if not t.startswith("|"): continue
        celdas = [c.strip() for c in t.strip("|").split("|")]
        if header is None:
            nl = [c.lower() for c in celdas]
            if any("tipo" in c for c in nl) and any("id" in c for c in nl):
                header = i
                for j, c in enumerate(nl):
                    if c == "id": cols["id"] = j
                    elif "tipo" in c: cols["tipo"] = j
                    elif "descripci" in c: cols["desc"] = j
                    elif "comprometida" in c or "compromet" in c: cols["fecha"] = j
                    elif "estado" in c: cols["estado"] = j
                    elif "responsable" in c: cols["resp"] = j
        elif header is not None and i == header + 1:
            continue
        elif header is not None:
            if not any(c for c in celdas): break
            tipo = celdas[cols.get("tipo", 1)] if cols.get("tipo") is not None else ""
            estado = celdas[cols.get("estado", 8)] if cols.get("estado") is not None else ""
            fecha = celdas[cols.get("fecha", 7)] if cols.get("fecha") is not None else ""
            if "CERRADO" in estado.upper():
                continue
            if not fecha or len(fecha) < 10:
                continue
            id_ = celdas[cols.get("id", 0)] if cols.get("id") is not None else ""
            desc = celdas[cols.get("desc", 2)] if cols.get("desc") is not None else ""
            resp = celdas[cols.get("resp", 5)] if cols.get("resp") is not None else ""
            if fecha < hoy:
                vencidas.append((id_, tipo, desc[:40], fecha, resp))
            elif fecha <= hoy[:8][:6] + "31":  # dentro del mes
                proximas.append((id_, tipo, desc[:40], fecha, resp))
    lineas_out = [f"# CHECK_INF — {hoy}", ""]
    if vencidas:
        lineas_out += ["## VENCIDAS", "", "| ID | Tipo | Descripción | Fecha comprometida | Responsable |", "|---|---|---|---|---|"]
        for row in vencidas:
            lineas_out.append(f"| {row[0]} | {row[1]} | {row[2]} | **{row[3]}** ⚠ | {row[4]} |")
    if proximas:
        lineas_out += ["", "## Vencen este mes", "", "| ID | Tipo | Descripción | Fecha comprometida | Responsable |", "|---|---|---|---|---|"]
        for row in proximas:
            lineas_out.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |")
    if not vencidas and not proximas:
        lineas_out.append("Sin incidencias INF vencidas ni próximas a vencer.")
    texto = "\n".join(lineas_out) + "\n"
    print(texto)
    return vencidas, proximas


def cli_check_inf(argv=None):
    p = _parser("Lista incidencias tipo INF vencidas o próximas a vencer en ISSUE_LOG.md (G5).")
    a = p.parse_args(argv)
    check_inf(_raiz(a))
    return 0


# --------------------------------------------------------------------------------- DASHBOARD (G8)
def dashboard(raiz, salida=None):
    """Genera un dashboard de una página en Markdown con los indicadores clave del proyecto (G8)."""
    lme = W.LME(raiz)
    ledgers = W.todos_los_ledgers(raiz)
    hoy = W.hoy()
    fase, emision_activa, proxima_puerta = W.fase_limitada(ledgers, raiz)
    paquetes = sorted(set(lme.paquetes()) | set(ledgers))
    total = len(paquetes)
    conteo = {"ENGINEERING": 0, "FOR_REVIEW": 0, "FOR_AUDIT": 0, "RELEASED": 0}
    for pq in paquetes:
        led = ledgers.get(pq)
        est = led["estado"] if led else "ENGINEERING"
        conteo[est] = conteo.get(est, 0) + 1
    pct = round(conteo["RELEASED"] / total * 100) if total else 0
    barra_total = 20
    barra_llena = round(pct / 100 * barra_total)
    barra = "█" * barra_llena + "░" * (barra_total - barra_llena)
    # incidencias abiertas
    def _contar_abiertas():
        p = os.path.join(raiz, W.DIR_GES, "ISSUE_LOG.md")
        if not os.path.exists(p): return 0
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        return txt.upper().count("ABIERTO") + txt.upper().count("EN CURSO")
    abiertas = _contar_abiertas()
    # riesgos activos (RIE-nnn)
    def _contar_riesgos():
        p = os.path.join(raiz, W.DIR_GES, "ASSUMPTIONS_AND_DECISIONS.md")
        if not os.path.exists(p): return 0
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        import re as re_
        return len(set(re_.findall(r"RIE-\d+", txt)))
    riesgos = _contar_riesgos()
    lineas = [
        "# DASHBOARD DEL PROYECTO",
        "",
        f"> {hoy} · Generado por DASHBOARD.py · no se edita",
        "",
        "```",
        f"  Fase: {fase:<8}  Emisión: {emision_activa or '—':<10}  Próxima puerta: {proxima_puerta}",
        "",
        f"  Avance  [{barra}] {pct}%  ({conteo['RELEASED']}/{total} paquetes RELEASED)",
        "",
        f"  Ingeniería: {conteo['ENGINEERING']:>3}   Revisión: {conteo['FOR_REVIEW']:>3}   Auditoría: {conteo['FOR_AUDIT']:>3}   Liberados: {conteo['RELEASED']:>3}",
        "",
        f"  Incidencias abiertas: {abiertas}   Riesgos registrados: {riesgos}",
        "```",
        "",
        "| Indicador | Detalle |",
        "|---|---|",
        f"| Paquetes por estado | ING {conteo['ENGINEERING']} · REV {conteo['FOR_REVIEW']} · AUD {conteo['FOR_AUDIT']} · REL {conteo['RELEASED']} |",
        f"| % completado | {pct} % |",
        f"| Incidencias abiertas | {abiertas} (ver ISSUE_LOG.md) |",
        f"| Riesgos RIE-nnn | {riesgos} (ver ASSUMPTIONS_AND_DECISIONS.md) |",
        f"| Próxima puerta | {proxima_puerta} |",
        "",
    ]
    texto = "\n".join(lineas) + "\n"
    if salida:
        with open(salida, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print(f"Dashboard escrito en {salida}.")
    else:
        print(texto)
    return texto


def cli_dashboard(argv=None):
    p = _parser("Genera un dashboard de una página con los indicadores clave del proyecto (G8).")
    p.add_argument("--salida", metavar="RUTA.md", help="escribe en archivo en lugar de stdout")
    a = p.parse_args(argv)
    dashboard(_raiz(a), a.salida)
    return 0

