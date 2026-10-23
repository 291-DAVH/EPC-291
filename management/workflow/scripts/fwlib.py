#!/usr/bin/env python3
"""fwlib.py — biblioteca común de los scripts de flujo del framework (WF-001).

El ESTADO de un paquete de revisión (PQ-nn) es la UBICACIÓN física de sus archivos:

    03_ENGINEERING                    ENGINEERING   (único lugar de trabajo; el único donde se edita)
    04_REVIEW/Review_Packages/PQ-nn   FOR_REVIEW    (congelado: hash SHA-256 registrado)
    05_AUDIT/Audit_Packages/PQ-nn     FOR_AUDIT     (congelado)
    06_RELEASED/PQ-nn                 RELEASED      (aprobado por auditoría; congelado)
    07_DELIVERABLES/<emisión>/...     copia rotulada (Rev 00 / Rev 01), solo lectura

Reglas que esta biblioteca hace cumplir:
  * Solo el resultado APPROVED permite avanzar de una etapa a la siguiente.
  * Todo paquete cuyos archivos difieren del manifiesto (hash) vuelve a Ingeniería.
  * Ningún script edita contenido de documentos: solo mueve, copia, renombra y registra.

Solo biblioteca estándar. No hace commits ni toca git.
"""
import datetime
import hashlib
import json
import os
import re
import shutil

__version__ = "1.1.0"

STATES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "states.json")

DIR_ING = "03_ENGINEERING"
DIR_REV = os.path.join("04_REVIEW", "Review_Packages")
DIR_AUD = os.path.join("05_AUDIT", "Audit_Packages")
DIR_REL = "06_RELEASED"
DIR_ENT = "07_DELIVERABLES"
DIR_GES = "90_MANAGEMENT"
DIR_LED = os.path.join(DIR_GES, "LEDGER")

ESTADOS = ("ENGINEERING", "FOR_REVIEW", "FOR_AUDIT", "RELEASED")
BASES = {"ENGINEERING": DIR_ING, "FOR_REVIEW": DIR_REV, "FOR_AUDIT": DIR_AUD, "RELEASED": DIR_REL}
OMITIR_EN_ING = {"Archive", "Temporary", ".git", "__pycache__"}
RESULTADOS = ("APPROVED", "APPROVED_WITH_COMMENTS", "REJECTED_WITH_COMMENTS", "REJECTED")
EMISIONES = ("IFR", "IFA", "IFC", "AS_BUILT")
CARPETA_EMISION = {"IFR": "IFR", "IFA": "IFA", "IFC": "IFC", "AS_BUILT": "AS_BUILT"}
ESTADO_DOC = {"ENGINEERING": "DRAFT", "FOR_REVIEW": "FOR_REVIEW", "FOR_AUDIT": "FOR_AUDIT", "RELEASED": "AUDITED"}

CODIGO = r"[A-Z][A-Z0-9]{1,7}-[A-Z]{1,2}-[A-Z]{2}-\d{3}"
RE_REV_NOMBRE = re.compile(r"_Rev(\d{2}(?:\.\d+){0,2}(?:\.(?:IC|IB|ID|IE))?)(?=[._]|$)")
RE_PQ = re.compile(r"^PQ-\d{2}$")


class FwError(Exception):
    """Error de regla del flujo: el script no hace nada y explica por qué."""


# --------------------------------------------------------------------------------- utilidades
def hoy():
    return os.environ.get("FW_FECHA") or datetime.date.today().strftime("%Y-%m-%d")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def norm(s):
    return (s or "").replace("`", "").strip()


def sin_acentos(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def encontrar_raiz(inicio=None):
    d = os.path.abspath(inicio or os.getcwd())
    while True:
        if os.path.isdir(os.path.join(d, DIR_ING)) and os.path.isdir(os.path.join(d, DIR_GES)):
            return d
        p = os.path.dirname(d)
        if p == d:
            raise FwError("No se encontró la raíz del proyecto (carpetas 03_ENGINEERING y 90_MANAGEMENT). Use --root.")
        d = p


def validar_pq(pq):
    pq = pq.strip().upper()
    if not RE_PQ.match(pq):
        raise FwError(f"Identificador de paquete inválido: «{pq}» (formato PQ-nn).")
    return pq


def archivos_de(base, rels_o_dirs=None):
    """Lista de rutas relativas (con '/') de los archivos bajo base (todo, o solo bajo rels_o_dirs)."""
    out = []
    if not os.path.isdir(base):
        return out
    for dp, dn, fn in os.walk(base):
        dn[:] = sorted(d for d in dn if d not in OMITIR_EN_ING)
        for f in sorted(fn):
            if f == ".gitkeep":
                continue
            out.append(os.path.relpath(os.path.join(dp, f), base).replace(os.sep, "/"))
    return out


def podar_vacias(base, rel):
    """Elimina directorios vacíos desde rel hacia arriba, sin tocar los de primer nivel bajo base."""
    base = os.path.abspath(base)
    d = os.path.abspath(os.path.dirname(os.path.join(base, rel)))
    while d != base and os.path.dirname(d) != base:
        try:
            os.rmdir(d)
        except OSError:
            break
        d = os.path.dirname(d)


# --------------------------------------------------------------------------------- LME
class LME:
    """Lectura/escritura mínima de la tabla de la Lista Maestra de Entregables (sección 8)."""

    CLAVES = (("id", "id"), ("codigo", "codigo"), ("aplica", "aplica"), ("paquete", "paquete"),
              ("depende", "depende"), ("estado", "estado"), ("rev.", "rev"), ("emision", "emision"),
              ("entrega (", "entrega"), ("auditado", "auditado"), ("ruta", "ruta"))

    def __init__(self, raiz):
        self.ruta = os.path.join(raiz, DIR_GES, "DELIVERABLES.md")
        self.lineas = []
        self.cols = {}
        self.filas = []          # {"n": índice de línea, "c": celdas (lista de str sin bordes)}
        if os.path.exists(self.ruta):
            with open(self.ruta, encoding="utf-8", newline="") as f:
                self.lineas = f.read().split("\n")
            self._parsear()

    def _celdas(self, linea):
        t = linea.strip()
        if not t.startswith("|"):
            return None
        return [c.strip() for c in t.strip("|").split("|")]

    def _parsear(self):
        h = None
        for i, l in enumerate(self.lineas):
            c = self._celdas(l)
            if c and any(sin_acentos(norm(x)).lower().startswith("codigo") for x in c) and \
                    any(norm(x).lower().startswith("paquete") for x in c):
                h = i
                break
        if h is None:
            return
        for j, nombre in enumerate(self._celdas(self.lineas[h])):
            n = sin_acentos(norm(nombre)).lower()
            for pref, clave in self.CLAVES:
                if n.startswith(pref) and clave not in self.cols:
                    self.cols[clave] = j
                    break
        i = h + 2
        while i < len(self.lineas):
            c = self._celdas(self.lineas[i])
            if c is None:
                break
            if len(c) == len(self._celdas(self.lineas[h])):
                self.filas.append({"n": i, "c": c})
            i += 1

    def valor(self, fila, clave):
        j = self.cols.get(clave)
        return norm(fila["c"][j]) if j is not None else ""

    def aplica(self, fila):
        return sin_acentos(self.valor(fila, "aplica")).upper() not in ("NO", "N")

    def codigo_valido(self, fila):
        return re.fullmatch(CODIGO, self.valor(fila, "codigo")) is not None

    def paquete(self, fila):
        m = re.search(r"PQ-\d{2}", self.valor(fila, "paquete"))
        return m.group(0) if m else None

    def filas_de(self, pq):
        return [f for f in self.filas if self.paquete(f) == pq and self.aplica(f) and self.codigo_valido(f)]

    def paquetes(self):
        return sorted({self.paquete(f) for f in self.filas if self.paquete(f) and self.aplica(f)})

    def dependencias(self, pq):
        dep = set()
        for f in self.filas_de(pq):
            dep.update(re.findall(r"PQ-\d{2}", self.valor(f, "depende")))
        dep.discard(pq)
        return sorted(dep)

    def emision(self, pq):
        for f in self.filas_de(pq):
            m = re.search(r"\b(IFA|IFC|IFR|AS[_ -]?BUILT)\b", self.valor(f, "emision").upper())
            if m:
                return m.group(1).replace(" ", "_").replace("-", "_")
        return None

    def poner(self, pq, clave, valor):
        """Escribe `valor` en la columna `clave` de todas las filas del paquete. Devuelve cuántas."""
        j = self.cols.get(clave)
        if j is None:
            return 0
        n = 0
        for f in self.filas_de(pq):
            f["c"][j] = valor
            n += 1
        return n

    def guardar(self):
        if not self.filas:
            return
        for f in self.filas:
            self.lineas[f["n"]] = "| " + " | ".join(f["c"]) + " |"
        with open(self.ruta, "w", encoding="utf-8", newline="") as fh:
            fh.write("\n".join(self.lineas))


# --------------------------------------------------------------------------------- ledger
def ruta_ledger(raiz, pq):
    return os.path.join(raiz, DIR_LED, f"{pq}.json")


def leer_ledger(raiz, pq):
    p = ruta_ledger(raiz, pq)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir_ledger(raiz, led):
    os.makedirs(os.path.join(raiz, DIR_LED), exist_ok=True)
    with open(ruta_ledger(raiz, led["pq"]), "w", encoding="utf-8", newline="\n") as f:
        json.dump(led, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def todos_los_ledgers(raiz):
    d = os.path.join(raiz, DIR_LED)
    out = {}
    if os.path.isdir(d):
        for n in sorted(os.listdir(d)):
            m = re.fullmatch(r"(PQ-\d{2})\.json", n)
            if m:
                out[m.group(1)] = leer_ledger(raiz, m.group(1))
    return out


def nuevo_ledger(pq):
    return {"pq": pq, "estado": "ENGINEERING", "emision": None, "ronda": 0, "fecha_envio": None,
            "extras": [], "miembros": {}, "emitido": [], "historial": []}


def evento(raiz, led, que, de, a, detalle="", fecha=None):
    """Anota el evento en el ledger del paquete y en 90_MANAGEMENT/LEDGER/EVENTS.md."""
    fecha = fecha or hoy()
    led["historial"].append({"fecha": fecha, "evento": que, "de": de, "a": a, "detalle": detalle})
    p = os.path.join(raiz, DIR_LED, "EVENTS.md")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    nuevo = not os.path.exists(p)
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        if nuevo:
            f.write("# EVENTOS — registro de movimientos de paquetes\n\n"
                    "> Generado por los scripts de `.claude/hooks/`. No se edita a mano.\n\n"
                    "| Fecha | Paquete | Evento | De | A | Detalle |\n|---|---|---|---|---|---|\n")
        f.write(f"| {fecha} | {led['pq']} | {que} | {de or '—'} | {a or '—'} | {detalle.replace('|', '/')} |\n")


def nota_changelog(raiz, texto):
    p = os.path.join(raiz, "CHANGELOG.md")
    enc = "## Movimientos de paquetes"
    s = "# CHANGELOG\n"
    if os.path.exists(p):
        with open(p, encoding="utf-8", newline="") as f:
            s = f.read()
    if enc not in s:
        s = s.rstrip("\n") + f"\n\n{enc}\n\n"
    s = s.rstrip("\n") + f"\n- {hoy()} — {texto}\n"
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


# --------------------------------------------------------------------------------- miembros / ubicación
def archivos_del_codigo(base, codigo):
    pat = re.compile("^" + re.escape(codigo) + r"(?![A-Z0-9-])")
    return [r for r in archivos_de(base) if pat.match(os.path.basename(r))]


def descubrir_miembros(raiz, lme, pq, extras):
    """Archivos de trabajo del paquete en 03_ENGINEERING (por código de la LME + extras declarados)."""
    base = os.path.join(raiz, DIR_ING)
    filas = lme.filas_de(pq)
    if not filas:
        raise FwError(f"{pq} no tiene entregables aplicables en la LME (90_MANAGEMENT/DELIVERABLES.md).")
    rels, faltan = [], []
    for f in filas:
        cod = lme.valor(f, "codigo")
        hallados = archivos_del_codigo(base, cod)
        if not hallados:
            faltan.append(cod)
        rels.extend(hallados)
    if faltan:
        raise FwError(f"{pq}: no hay archivos en 03_ENGINEERING para: {', '.join(faltan)}.")
    for e in extras:
        e = e.replace("\\", "/").strip("/")
        p = os.path.join(base, e)
        if os.path.isfile(p):
            rels.append(e)
        elif os.path.isdir(p):
            rels.extend(f"{e}/{r}" for r in archivos_de(p))
        else:
            raise FwError(f"{pq}: el extra «{e}» no existe en 03_ENGINEERING.")
    rels = sorted(set(rels))
    # un DWG viaja con su PDF (el PDF es lo que se revisa)
    for r in rels:
        if r.lower().endswith(".dwg") and "xref" not in os.path.basename(r).lower():
            stem = r[:-4]
            if not any(x.lower() == stem.lower() + ".pdf" for x in rels):
                raise FwError(f"{pq}: el DWG «{r}» no tiene su PDF «{os.path.basename(stem)}.pdf» en el paquete. "
                              "El usuario debe enviar DWG + XREF + PDF; Claude revisa solo el PDF.")
    return rels


def ubicaciones(raiz, led):
    """Devuelve (estado, detalle). estado ∈ ESTADOS | 'INCONSISTENTE'."""
    presentes = {}
    for est in ESTADOS:
        base = os.path.join(raiz, BASES[est]) if est == "ENGINEERING" else os.path.join(raiz, BASES[est], led["pq"])
        presentes[est] = [r for r in led["miembros"] if os.path.isfile(os.path.join(base, r))]
    total = len(led["miembros"])
    llenos = [e for e in ESTADOS if len(presentes[e]) == total and total]
    parciales = [e for e in ESTADOS if presentes[e] and len(presentes[e]) != total]
    if len(llenos) == 1 and not parciales:
        return llenos[0], ""
    det = "; ".join(f"{e}: {len(presentes[e])}/{total}" for e in ESTADOS if presentes[e])
    if len(llenos) == 1:
        return llenos[0], "copias sueltas en " + det
    return "INCONSISTENTE", det or "sin archivos"


def base_de(raiz, pq, estado):
    return os.path.join(raiz, DIR_ING) if estado == "ENGINEERING" else os.path.join(raiz, BASES[estado], pq)


def hash_ok(raiz, led, estado):
    """Compara los archivos en `estado` con el manifiesto. Devuelve lista de diferencias."""
    base = base_de(raiz, led["pq"], estado)
    dif = []
    for r, m in led["miembros"].items():
        p = os.path.join(base, r)
        if not os.path.isfile(p):
            dif.append(f"falta {r}")
        elif sha256(p) != m["sha256"]:
            dif.append(f"MODIFICADO {r}")
    return dif


def mover(raiz, led, origen, destino):
    """Mueve todos los miembros de `origen` a `destino` (con reversión si algo falla)."""
    bo, bd = base_de(raiz, led["pq"], origen), base_de(raiz, led["pq"], destino)
    hechos = []
    try:
        for r in sorted(led["miembros"]):
            s, d = os.path.join(bo, r), os.path.join(bd, r)
            if os.path.exists(d):
                raise FwError(f"{led['pq']}: ya existe «{r}» en el destino ({destino}).")
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.move(s, d)
            hechos.append((s, d))
    except Exception:
        for s, d in reversed(hechos):
            os.makedirs(os.path.dirname(s), exist_ok=True)
            shutil.move(d, s)
        raise
    for r in led["miembros"]:
        podar_vacias(bo, r)
    if origen != "ENGINEERING" and os.path.isdir(bo) and not archivos_de(bo):
        shutil.rmtree(bo, ignore_errors=True)


def manifiesto(raiz, rels):
    base = os.path.join(raiz, DIR_ING)
    out = {}
    for r in rels:
        p = os.path.join(base, r)
        out[r] = {"sha256": sha256(p), "size": os.path.getsize(p)}
    return out


# --------------------------------------------------------------------------------- resultados
def leer_resultado(path):
    """Último campo `Resultado:` válido de un archivo; None si no hay."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    ms = re.findall(r"^\s*[-*>]*\s*\**Resultado\**\s*:\s*\**\s*`?([A-Z_]+)`?", txt, re.MULTILINE)
    ms = [m for m in ms if m in RESULTADOS]
    return ms[-1] if ms else None


def _fecha_en_nombre(n):
    m = re.search(r"_(\d{8})", n)
    if not m:
        return None
    d = m.group(1)
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def hoja_vigente(raiz, pq):
    """Hoja de revisión más reciente del paquete: (ruta, resultado, fecha) o None."""
    d = os.path.join(raiz, "04_REVIEW", "Review_Sheets")
    if not os.path.isdir(d):
        return None
    hojas = sorted(n for n in os.listdir(d) if re.fullmatch(rf"REVIEW-\d+_\d{{8}}_{pq}\.md", n))
    if not hojas:
        return None
    n = hojas[-1]
    return os.path.join(d, n), leer_resultado(os.path.join(d, n)), _fecha_en_nombre(n)


def informes_auditoria(raiz):
    d = os.path.join(raiz, "05_AUDIT", "Audit_Reports")
    out = []
    if os.path.isdir(d):
        for n in sorted(os.listdir(d)):
            if re.fullmatch(r"AUD-\d+_\d{8}\.md", n):
                p = os.path.join(d, n)
                with open(p, encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
                em = re.search(r"^\s*[-*>]*\s*\**Emisi[oó]n\**\s*:\s*\**\s*`?(IFR|IFA|IFC|AS_BUILT)`?", txt, re.M)
                pqs = re.search(r"^\s*[-*>]*\s*\**Paquetes\**\s*:\s*(.+)$", txt, re.M)
                out.append({"id": n.split("_")[0], "ruta": p, "fecha": _fecha_en_nombre(n),
                            "emision": em.group(1) if em else None,
                            "paquetes": sorted(set(re.findall(r"PQ-\d{2}", pqs.group(1)))) if pqs else [],
                            "resultado": leer_resultado(p)})
    return out


def siguiente_tr(raiz):
    mx = 0
    d = os.path.join(raiz, DIR_ENT, "TRANSMITTALS")
    if os.path.isdir(d):
        for n in os.listdir(d):
            m = re.match(r"TR-(\d+)", n)
            if m:
                mx = max(mx, int(m.group(1)))
    for led in todos_los_ledgers(raiz).values():
        for e in led["emitido"]:
            m = re.match(r"TR-(\d+)", e["tr"])
            if m:
                mx = max(mx, int(m.group(1)))
    return f"TR-{mx + 1:03d}"


def conjunto_pendiente(raiz, emision):
    """PQ con ledger de la emisión dada, que todavía no fueron emitidos en su ronda actual."""
    out = []
    for pq, led in todos_los_ledgers(raiz).items():
        if led["emision"] == emision and not any(e["emision"] == emision and e["ronda"] == led["ronda"]
                                                 for e in led["emitido"]):
            out.append(pq)
    return out


def paquetes_faltantes(raiz, lme, emision):
    """PQ de la LME con esa emisión objetivo que aún no tienen ledger de esa emisión."""
    led = todos_los_ledgers(raiz)
    return [pq for pq in lme.paquetes() if lme.emision(pq) == emision
            and (pq not in led or led[pq]["emision"] != emision)]


def correr(main):
    import sys
    try:
        sys.exit(main() or 0)
    except FwError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

# --------------------------------------------------------------------------------- M4 / M7 / A1 / A4
def leer_states():
    """Lee states.json (fuente única de la máquina de estados). Devuelve dict o None."""
    if os.path.exists(STATES_FILE):
        with open(STATES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None


def escribir_states(raiz=None):
    """Crea / actualiza states.json con la versión actual del motor."""
    data = {
        "version": __version__,
        "estados": list(ESTADOS),
        "resultados": list(RESULTADOS),
        "emisiones": list(EMISIONES),
        "estado_doc": ESTADO_DOC,
        "transiciones": [
            {"de": "ENGINEERING", "a": "FOR_REVIEW", "script": "SEND_TO_REVIEW.py"},
            {"de": "FOR_REVIEW",  "a": "FOR_AUDIT",  "script": "SEND_TO_AUDIT.py"},
            {"de": "FOR_AUDIT",   "a": "RELEASED",   "script": "APPROVE_AUDIT.py"},
            {"de": "*",           "a": "ENGINEERING","script": "RETURN_TO_ENGINEERING.py"},
        ],
    }
    target = STATES_FILE
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    return data


def verificar_version():
    """Avisa si states.json existe y su versión difiere del motor. Devuelve lista de avisos."""
    st = leer_states()
    if st and st.get("version") != __version__:
        return [f"states.json versión {st['version']} ≠ motor {__version__}: ejecute CHECK_STATE.py --actualizar-states."]
    return []


def validar_dec_existe(raiz, dec_id):
    """Verifica que dec_id (p.ej. DEC-007) esté en ASSUMPTIONS_AND_DECISIONS.md. No bloquea si el archivo no existe."""
    if not dec_id:
        return
    p = os.path.join(raiz, DIR_GES, "ASSUMPTIONS_AND_DECISIONS.md")
    if not os.path.exists(p):
        return  # sin registro no podemos validar; el usuario es responsable
    with open(p, encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    if dec_id not in txt:
        raise FwError(
            f"La decisión «{dec_id}» no aparece en 90_MANAGEMENT/ASSUMPTIONS_AND_DECISIONS.md. "
            "Regístrela allí antes de usar --permitir-varios o --solo-documental."
        )


def fase_proyecto(ledgers):
    """Infiere la fase PM² del proyecto desde el estado de los ledgers.
    Devuelve ("IC"|"IB"|"ID"|"IE"|"ASB", emision_activa, proxima_puerta).
    """
    if not ledgers:
        return "IC", None, "aprobar inicio ●"
    emitidas = set()
    emisiones_activas = set()
    for l in ledgers.values():
        for e in l.get("emitido", []):
            if e.get("confirmado"):
                emitidas.add(e["emision"])
        if l.get("emision"):
            emisiones_activas.add(l["emision"])
    if "AS_BUILT" in emitidas:
        return "ASB", "AS_BUILT", "aceptación firmada ●"
    if "AS_BUILT" in emisiones_activas:
        return "ASB", "AS_BUILT", "entregar AS_BUILT"
    if "IFC" in emitidas:
        return "IE", "IFC", "aceptación firmada ●"
    if "IFA" in emitidas:
        return "IE", "IFA", "entregar IFC o iniciar as-built"
    if "IFC" in emisiones_activas:
        return "ID", "IFC", "auditar y emitir IFC"
    if "IFA" in emisiones_activas:
        return "ID", "IFA", "auditar y emitir IFA"
    if "IFR" in emisiones_activas or any(l.get("ronda", 0) > 0 for l in ledgers.values()):
        return "IB", "IFR", "auditar y emitir IFR"
    return "IC", None, "aprobar plan de paquetes ●"

