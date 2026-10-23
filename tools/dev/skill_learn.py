#!/usr/bin/env python3 -B
"""
skill_learn.py — Sistema de aprendizaje incremental para Skills del framework.

Uso:
  python -B skill_learn.py <skill_name> learn [archivo]
  python -B skill_learn.py <skill_name> learn --modified
  python -B skill_learn.py <skill_name> relearn
  python -B skill_learn.py <skill_name> status
  python -B skill_learn.py <skill_name> export dxf <output_file>

El script vive en .claude/library/core/ y opera sobre:
  .claude/skills/<skill_name>/knowledge/   — archivos de conocimiento del usuario
  .claude/skills/<skill_name>/learning/    — inventario de hashes (inventory.json)
  .claude/skills/<skill_name>/memory/      — memoria semántica generada (offline)
  .claude/skills/<skill_name>/cache/       — caché temporal
"""

import sys
import os
import re
import json
import hashlib
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

SCRIPT_DIR  = Path(__file__).resolve().parent          # .claude/library/core/
CLAUDE_DIR  = SCRIPT_DIR.parent.parent                 # .claude/
SKILLS_DIR  = CLAUDE_DIR / "skills"


def get_skill_paths(skill_name: str) -> dict:
    skill_root = SKILLS_DIR / skill_name
    if not skill_root.exists():
        raise FileNotFoundError(f"Skill '{skill_name}' no existe en {SKILLS_DIR}")
    return {
        "root":      skill_root,
        "knowledge": skill_root / "knowledge",
        "learning":  skill_root / "learning",
        "memory":    skill_root / "memory",
        "cache":     skill_root / "cache",
        "skill_json": skill_root / "skill.json",
        "inventory": skill_root / "learning" / "inventory.json",
    }


# ---------------------------------------------------------------------------
# Inventario de hashes
# ---------------------------------------------------------------------------

def load_inventory(paths: dict) -> dict:
    inv_path = paths["inventory"]
    if inv_path.exists():
        with open(inv_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "1.0", "files": {}}


def save_inventory(paths: dict, inventory: dict):
    paths["inventory"].parent.mkdir(parents=True, exist_ok=True)
    with open(paths["inventory"], "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)


def file_hash(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ---------------------------------------------------------------------------
# Descubrimiento de archivos en knowledge/
# ---------------------------------------------------------------------------

LEARNABLE_EXTENSIONS = {".pdf", ".svg", ".dxf", ".md", ".txt", ".xlsx",
                        ".png", ".jpg", ".jpeg", ".json", ".csv", ".docx"}


def discover_knowledge_files(paths: dict) -> list:
    knowledge_dir = paths["knowledge"]
    if not knowledge_dir.exists():
        return []
    files = []
    for f in knowledge_dir.rglob("*"):
        if f.is_file() and f.name != ".gitkeep" and f.suffix.lower() in LEARNABLE_EXTENSIONS:
            files.append(f)
    return sorted(files)


def relative_key(filepath: Path, base: Path) -> str:
    return str(filepath.relative_to(base)).replace("\\", "/")


# ---------------------------------------------------------------------------
# Helpers de extracción de contenido técnico
# ---------------------------------------------------------------------------

# Disciplinas por patrones en nombre de archivo y contenido
DISCIPLINE_PATTERNS = {
    "E":  ["electr", "tablero", "cable", "interruptor", "transformador", "baja tension",
           "alta tension", "media tension", "unifilar", "multifilar", "sld", "mld",
           "proteccion", "conductor", "circuito", "corriente", "voltaje", "tension"],
    "FP": ["incendio", "sprinkler", "hidrante", "extintor", "supresion", "rociador",
           "nfpa", "fire", "combate"],
    "FD": ["deteccion", "alarma", "detector", "sensor humo", "panel de incendio"],
    "H":  ["hvac", "climatizacion", "ventilacion", "aire acondicionado", "calefaccion",
           "ashrae", "caudal aire", "ducto", "extractor"],
    "M":  ["mecanico", "bomba", "compresor", "ventilador", "turbina", "transmision mecanica"],
    "TM": ["termomecanico", "caldera", "intercambiador", "presion vapor", "fluido termico"],
    "PL": ["cañeria", "tuberia", "hidraulico", "sanitario", "agua potable", "cloacal",
           "pluvial", "drenaje", "valvula", "fitting"],
    "I":  ["instrumentacion", "control", "pid", "instrumento", "transmisor", "medicion",
           "isa", "field bus", "scada", "dcs", "plc"],
    "T":  ["telecomunicaciones", "datos", "fibra", "ethernet", "cableado estructurado",
           "cctv", "red", "switch", "router"],
    "C":  ["civil", "estructura", "hormigon", "acero", "fundacion", "losa", "viga",
           "columna", "cirsoc"],
    "A":  ["arquitectura", "arquitectonico", "mamposteria", "revestimiento", "acabado"],
}


def detect_discipline(filename: str, text: str) -> str:
    """Detecta la disciplina principal a partir del nombre del archivo y el contenido."""
    combined = (filename + " " + text[:3000]).lower()
    scores = {}
    for disc, patterns in DISCIPLINE_PATTERNS.items():
        scores[disc] = sum(1 for p in patterns if p in combined)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "ND"


def extract_chapters(text: str) -> list:
    """Extrae capítulos numerados del texto (ej: '1. Alcance', '2 Materiales')."""
    patterns = [
        r'^\s*(\d+\.?\d*\.?\d*)\s+([A-ZÁÉÍÓÚÑ][^\n]{3,60})',  # "1. Alcance"
        r'^\s*CAPÍTULO\s+(\d+)[^\n]*:?\s*([A-ZÁÉÍÓÚÑ][^\n]{3,60})',
        r'^\s*SECCIÓN\s+(\d+)[^\n]*:?\s*([A-ZÁÉÍÓÚÑ][^\n]{3,60})',
    ]
    chapters = []
    seen = set()
    for line in text.splitlines():
        for pat in patterns:
            m = re.match(pat, line, re.IGNORECASE)
            if m:
                chapter = m.group(0).strip()[:80]
                if chapter not in seen:
                    chapters.append(chapter)
                    seen.add(chapter)
                break
    return chapters[:30]


def extract_norms(text: str) -> list:
    """Extrae referencias a normas técnicas (IEC, IRAM, ISO, NFPA, AEA, etc.)."""
    pattern = r'\b(IEC|IRAM|ISO|NFPA|AEA|ASHRAE|CIRSOC|NEC|IEEE|EN|UL|FM|API|ASME|ISA)\s*[\-–]?\s*\d[\d\-\./]*'
    found = re.findall(pattern, text, re.IGNORECASE)
    # Extraer la coincidencia completa
    full_matches = re.findall(
        r'\b(?:IEC|IRAM|ISO|NFPA|AEA|ASHRAE|CIRSOC|NEC|IEEE|EN|UL|FM|API|ASME|ISA)\s*[\-–]?\s*\d[\d\-\./A-Za-z]*',
        text, re.IGNORECASE
    )
    unique = list(dict.fromkeys(m.strip().upper() for m in full_matches))
    return unique[:30]


def extract_acceptance_criteria(text: str) -> list:
    """Extrae frases de criterios de aceptación."""
    keywords = ["criterio de aceptación", "criterio de rechazo", "ensayo de", "prueba de",
                "se verificará", "se comprobará", "deberá demostrar", "tolerancia",
                "deberá cumplir", "no deberá superar", "mínimo exigido"]
    lines_found = []
    for line in text.splitlines():
        if any(kw in line.lower() for kw in keywords):
            stripped = line.strip()
            if 20 < len(stripped) < 200:
                lines_found.append(stripped)
    return lines_found[:20]


def extract_materials_equipment(text: str) -> list:
    """Extrae menciones de materiales y equipos con especificaciones."""
    keywords = ["deberá ser", "será de tipo", "material:", "equipo:", "gabinete",
                "tablero", "cable tipo", "interruptor", "disyuntor", "seccion minima",
                "sección mínima", "grado de proteccion", "grado de protección", "ip "]
    lines_found = []
    for line in text.splitlines():
        if any(kw in line.lower() for kw in keywords):
            stripped = line.strip()
            if 15 < len(stripped) < 200:
                lines_found.append(stripped)
    return lines_found[:25]


# ---------------------------------------------------------------------------
# Estudio de un archivo — genera resumen semántico en memory/
# ---------------------------------------------------------------------------

def study_file(filepath: Path, paths: dict) -> str:
    """
    Estudia un archivo y escribe su resumen semántico en memory/.
    Para PDFs extrae texto completo para habilitar generación offline.
    """
    memory_dir = paths["memory"]
    memory_dir.mkdir(parents=True, exist_ok=True)

    rel = relative_key(filepath, paths["knowledge"])
    mem_name = rel.replace("/", "__").replace(".", "_") + ".md"
    mem_path = memory_dir / mem_name

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ext = filepath.suffix.lower()
    size_kb = filepath.stat().st_size / 1024

    lines = [
        f"# Memoria: {filepath.name}",
        f"",
        f"- **Archivo:** `{rel}`",
        f"- **Tipo:** `{ext}`",
        f"- **Tamaño:** {size_kb:.1f} KB",
        f"- **Estudiado:** {now}",
        f"",
    ]

    if ext == ".pdf":
        _study_pdf(filepath, lines, size_kb)

    elif ext in (".docx",):
        _study_docx(filepath, lines)

    elif ext == ".md":
        _study_md(filepath, lines)

    elif ext in (".txt", ".csv"):
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            lines.append("## Contenido")
            lines.append("```")
            lines.append(content[:3000])
            lines.append("```")
        except Exception as e:
            lines.append(f"[Error al leer: {e}]")

    elif ext == ".svg":
        _study_svg(filepath, lines)

    elif ext == ".dxf":
        lines.append(f"Archivo DXF — {size_kb:.1f} KB. Plantilla CAD para exportación.")

    elif ext == ".json":
        try:
            data = json.loads(filepath.read_text(encoding="utf-8", errors="ignore"))
            keys = list(data.keys())[:15] if isinstance(data, dict) else []
            lines.append(f"Archivo JSON — claves: {keys}")
        except Exception as e:
            lines.append(f"[Error al parsear JSON: {e}]")

    else:
        lines.append(f"Archivo binario ({ext}). Tamaño: {size_kb:.1f} KB.")

    lines.append("")
    mem_path.write_text("\n".join(lines), encoding="utf-8")
    return mem_name


def _study_pdf(filepath: Path, lines: list, size_kb: float):
    """Extrae texto de un PDF para memoria offline."""
    try:
        import pdfplumber
    except ImportError:
        lines.append("## Estado")
        lines.append("")
        lines.append("> **pdfplumber no instalado.** Instalar con: `pip install pdfplumber`")
        lines.append("> Sin extracción de texto — la generación offline no estará disponible.")
        lines.append(f"> Archivo: {filepath.name} ({size_kb:.1f} KB)")
        return

    try:
        text_pages = []
        with pdfplumber.open(filepath) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages[:50]):  # max 50 páginas
                t = page.extract_text()
                if t and t.strip():
                    text_pages.append(t)

        if not text_pages:
            lines.append("## Estado")
            lines.append("PDF sin texto extraíble (puede ser imagen escaneada).")
            lines.append(f"Páginas totales: {total_pages}")
            return

        full_text = "\n".join(text_pages)
        disc = detect_discipline(filepath.name, full_text)
        chapters = extract_chapters(full_text)
        norms = extract_norms(full_text)
        criteria = extract_acceptance_criteria(full_text)
        materials = extract_materials_equipment(full_text)

        lines.append(f"## Análisis")
        lines.append(f"")
        lines.append(f"- **Disciplina:** `{disc}`")
        lines.append(f"- **Páginas extraídas:** {len(text_pages)} de {total_pages}")
        lines.append(f"- **Caracteres:** {len(full_text):,}")
        lines.append(f"")

        if chapters:
            lines.append("## Estructura de capítulos")
            lines.append("")
            for c in chapters:
                lines.append(f"- {c}")
            lines.append("")

        if norms:
            lines.append("## Normas citadas")
            lines.append("")
            for n in norms:
                lines.append(f"- {n}")
            lines.append("")

        if criteria:
            lines.append("## Criterios de aceptación detectados")
            lines.append("")
            for c in criteria:
                lines.append(f"- {c}")
            lines.append("")

        if materials:
            lines.append("## Requisitos de materiales y equipos")
            lines.append("")
            for m in materials:
                lines.append(f"- {m}")
            lines.append("")

        # Contenido completo para referencia offline (primeros 8000 caracteres)
        lines.append("## Texto extraído (referencia offline)")
        lines.append("")
        lines.append("```")
        lines.append(full_text[:8000])
        if len(full_text) > 8000:
            lines.append(f"\n[... +{len(full_text)-8000:,} caracteres adicionales ...]")
        lines.append("```")

    except Exception as e:
        lines.append(f"## Error")
        lines.append(f"[Error al extraer PDF: {e}]")


def _study_docx(filepath: Path, lines: list):
    """Extrae texto de un DOCX."""
    try:
        import docx
        doc = docx.Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs)
        disc = detect_discipline(filepath.name, full_text)
        chapters = extract_chapters(full_text)
        norms = extract_norms(full_text)

        lines.append(f"## Análisis")
        lines.append(f"- **Disciplina:** `{disc}`")
        lines.append(f"- **Párrafos:** {len(paragraphs)}")
        lines.append("")

        if chapters:
            lines.append("## Capítulos detectados")
            for c in chapters:
                lines.append(f"- {c}")
            lines.append("")

        if norms:
            lines.append("## Normas citadas")
            for n in norms:
                lines.append(f"- {n}")
            lines.append("")

        lines.append("## Texto extraído")
        lines.append("```")
        lines.append(full_text[:6000])
        lines.append("```")

    except ImportError:
        lines.append("> **python-docx no instalado.** Instalar con: `pip install python-docx`")
    except Exception as e:
        lines.append(f"[Error al extraer DOCX: {e}]")


def _study_md(filepath: Path, lines: list):
    """Extrae contenido de un archivo Markdown."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        disc = detect_discipline(filepath.name, content)
        norms = extract_norms(content)
        headings = [l.strip() for l in content.splitlines() if l.startswith("#")][:20]

        lines.append(f"## Análisis")
        lines.append(f"- **Disciplina:** `{disc}`")
        lines.append(f"- **Caracteres:** {len(content):,}")
        lines.append("")

        if headings:
            lines.append("## Estructura")
            for h in headings:
                lines.append(f"- {h}")
            lines.append("")

        if norms:
            lines.append("## Normas citadas")
            for n in norms:
                lines.append(f"- {n}")
            lines.append("")

        lines.append("## Contenido")
        lines.append("```markdown")
        lines.append(content)
        lines.append("```")

    except Exception as e:
        lines.append(f"[Error al leer: {e}]")


def _study_svg(filepath: Path, lines: list):
    """Analiza un archivo SVG."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        size_kb = filepath.stat().st_size / 1024
        has_ports = 'id="ports"' in content
        has_labels = 'id="label_slots"' in content
        lines.append(f"Archivo SVG — {size_kb:.1f} KB.")
        lines.append(f"- Tiene grupo `ports`: {'Sí' if has_ports else 'No'}")
        lines.append(f"- Tiene grupo `label_slots`: {'Sí' if has_labels else 'No'}")
    except Exception as e:
        lines.append(f"[Error al analizar SVG: {e}]")


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------

def cmd_status(skill_name: str):
    paths = get_skill_paths(skill_name)
    inventory = load_inventory(paths)
    files = discover_knowledge_files(paths)

    studied_files = {k: v for k, v in inventory["files"].items() if v.get("studied")}
    pending = [f for f in files
               if relative_key(f, paths["knowledge"]) not in studied_files]

    modified = []
    for f in files:
        key = relative_key(f, paths["knowledge"])
        if key in studied_files:
            current_hash = file_hash(f)
            if current_hash != studied_files[key].get("hash", ""):
                modified.append(key)

    last_dates = [v.get("last_studied") for v in inventory["files"].values() if v.get("last_studied")]
    last_date = max(last_dates) if last_dates else "nunca"

    skill_json_path = paths["skill_json"]
    skill_data = {}
    if skill_json_path.exists():
        with open(skill_json_path, "r", encoding="utf-8") as f:
            skill_data = json.load(f)

    # Verificar pdfplumber
    try:
        import pdfplumber
        pdf_ok = "✓ disponible"
    except ImportError:
        pdf_ok = "✗ no instalado (pip install pdfplumber)"

    print(f"\n{'='*52}")
    print(f"  Skill: {skill_name}")
    print(f"  Versión: {skill_data.get('version', 'desconocida')}")
    print(f"{'='*52}")
    print(f"  Archivos en knowledge/: {len(files)}")
    print(f"  Archivos estudiados:    {len(studied_files)}")
    print(f"  Pendientes de estudio:  {len(pending)}")
    print(f"  Modificados:            {len(modified)}")
    print(f"  Último aprendizaje:     {last_date}")
    print(f"  Tipos:                  {', '.join(skill_data.get('learnable_content', []))}")
    print(f"  pdfplumber:             {pdf_ok}")
    if pending:
        print(f"\n  Pendientes:")
        for p in pending[:10]:
            print(f"    - {relative_key(p, paths['knowledge'])}")
    if modified:
        print(f"\n  Modificados (usar 'learn --modified'):")
        for m in modified[:10]:
            print(f"    - {m}")
    print()


def cmd_learn(skill_name: str, target: str = None, modified_only: bool = False):
    paths = get_skill_paths(skill_name)
    inventory = load_inventory(paths)
    all_files = discover_knowledge_files(paths)

    if target:
        target_path = paths["knowledge"] / target
        if not target_path.exists():
            print(f"Error: '{target}' no encontrado en knowledge/")
            sys.exit(1)
        files_to_study = [target_path]
        print(f"[learn] Estudiando archivo específico: {target}")

    elif modified_only:
        files_to_study = []
        for f in all_files:
            key = relative_key(f, paths["knowledge"])
            if key in inventory["files"]:
                current_hash = file_hash(f)
                if current_hash != inventory["files"][key].get("hash", ""):
                    files_to_study.append(f)
        print(f"[learn --modified] {len(files_to_study)} archivo(s) modificado(s).")

    else:
        files_to_study = []
        for f in all_files:
            key = relative_key(f, paths["knowledge"])
            if key not in inventory["files"] or not inventory["files"][key].get("studied"):
                files_to_study.append(f)
            else:
                current_hash = file_hash(f)
                if current_hash != inventory["files"][key].get("hash", ""):
                    files_to_study.append(f)
        if not files_to_study:
            print(f"[learn] Sin cambios. Todos los archivos ya están estudiados.")
            return
        print(f"[learn] {len(files_to_study)} archivo(s) nuevo(s) o modificado(s).")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    for f in files_to_study:
        key = relative_key(f, paths["knowledge"])
        h = file_hash(f)
        print(f"  Estudiando: {key} ...", end=" ", flush=True)
        try:
            mem_name = study_file(f, paths)
            inventory["files"][key] = {
                "hash": h,
                "studied": True,
                "last_studied": now,
                "memory_file": mem_name
            }
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")
            inventory["files"][key] = {
                "hash": h,
                "studied": False,
                "last_studied": now,
                "error": str(e)
            }

    save_inventory(paths, inventory)
    print(f"[learn] Inventario actualizado → {paths['inventory']}")
    _generate_index(skill_name, paths, inventory)


def cmd_relearn(skill_name: str):
    paths = get_skill_paths(skill_name)

    for d in [paths["cache"], paths["memory"]]:
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and f.name != ".gitkeep":
                    f.unlink()
    save_inventory(paths, {"version": "1.0", "files": {}})

    print(f"[relearn] Índices, caché y memoria eliminados para '{skill_name}'.")
    print(f"[relearn] Iniciando re-estudio completo...")
    cmd_learn(skill_name)


def _generate_index(skill_name: str, paths: dict, inventory: dict):
    """
    Genera memory/INDEX.md — índice organizado por disciplina y tipo.
    Este archivo es la entrada principal para generación offline.
    """
    memory_dir = paths["memory"]
    memory_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    studied = {k: v for k, v in inventory["files"].items() if v.get("studied")}

    # Agrupar por tipo
    by_type = {}
    for key in studied:
        ext = Path(key).suffix.lower()
        by_type.setdefault(ext, []).append(key)

    # Intentar leer disciplina de cada memory file
    by_disc = {}
    for key, meta in studied.items():
        mem_file = meta.get("memory_file", "")
        mem_path = memory_dir / mem_file
        disc = "ND"
        if mem_path.exists():
            content = mem_path.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'\*\*Disciplina:\*\*\s*`([^`]+)`', content)
            if m:
                disc = m.group(1)
        by_disc.setdefault(disc, []).append(key)

    lines = [
        f"# Índice de conocimiento — {skill_name}",
        f"",
        f"Actualizado: {now}  |  Archivos estudiados: {len(studied)}",
        f"",
        f"## Instrucciones para Claude",
        f"",
        f"Este índice es la entrada offline para generación de pliegos.",
        f"Antes de redactar, leer los archivos de memoria de la disciplina relevante.",
        f"Los archivos `.md` en esta carpeta contienen texto extraído de los pliegos aprobados.",
        f"No inventar datos — usar solo lo que está documentado aquí.",
        f"",
    ]

    if by_disc and any(d != "ND" for d in by_disc):
        lines.append("## Por disciplina")
        lines.append("")
        for disc in sorted(by_disc.keys()):
            keys = by_disc[disc]
            lines.append(f"### Disciplina `{disc}` ({len(keys)} archivo(s))")
            for k in sorted(keys):
                mem_file = studied[k].get("memory_file", "")
                lines.append(f"- [{k}]({mem_file})")
            lines.append("")

    lines.append("## Por tipo de archivo")
    lines.append("")
    for ext, keys in sorted(by_type.items()):
        lines.append(f"### `{ext}` ({len(keys)} archivo(s))")
        for k in sorted(keys):
            mem_file = studied[k].get("memory_file", "")
            lines.append(f"- [{k}]({mem_file})")
        lines.append("")

    if not studied:
        lines.append("_Sin archivos estudiados aún. Usar `skill learn` para entrenar._")
        lines.append("")
        lines.append("Para instalar el extractor de PDF:")
        lines.append("```")
        lines.append("pip install pdfplumber")
        lines.append("```")

    (memory_dir / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[learn] Índice generado → {memory_dir / 'INDEX.md'}")


def cmd_export_dxf(skill_name: str, output_file: str):
    """
    Exporta/genera un DXF básico.
    Si el skill tiene una plantilla DXF en knowledge/dxf/, la usa como base.
    """
    paths = get_skill_paths(skill_name)
    dxf_dir = paths["knowledge"] / "dxf"
    templates = list(dxf_dir.glob("*.dxf")) if dxf_dir.exists() else []

    if templates:
        template = templates[0]
        print(f"[export dxf] Plantilla encontrada: {template.name}")
        print(f"[export dxf] Salida: {output_file}")
        print(f"[export dxf] Plantilla disponible en: {template}")
    else:
        print(f"[export dxf] Sin plantilla DXF en knowledge/dxf/. Generando DXF mínimo.")
        print(f"[export dxf] Para usar una plantilla corporativa: copiar el .dxf en:")
        print(f"[export dxf]   {dxf_dir}")
        print(f"[export dxf] Salida: {output_file}")

    print(f"[export dxf] Invocar create-electrical-line-diagram con parámetro export=dxf.")


# ---------------------------------------------------------------------------
# Entrada principal
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Uso: python -B skill_learn.py <skill_name> <comando> [opciones]")
        print("")
        print("Comandos:")
        print("  learn              Estudia archivos nuevos o modificados en knowledge/")
        print("  learn <archivo>    Estudia solo el archivo especificado")
        print("  learn --modified   Re-estudia solo los archivos modificados")
        print("  relearn            Borra todo y re-estudia desde cero")
        print("  status             Muestra estadísticas del estado de aprendizaje")
        print("  export dxf <out>   Exporta/genera un DXF (requiere diagrama activo)")
        sys.exit(1)

    skill_name = sys.argv[1]
    command    = sys.argv[2].lower()

    if command == "status":
        cmd_status(skill_name)

    elif command == "learn":
        extra = sys.argv[3] if len(sys.argv) > 3 else None
        if extra == "--modified":
            cmd_learn(skill_name, modified_only=True)
        elif extra and not extra.startswith("--"):
            cmd_learn(skill_name, target=extra)
        else:
            cmd_learn(skill_name)

    elif command == "relearn":
        cmd_relearn(skill_name)

    elif command == "export" and len(sys.argv) > 3 and sys.argv[3].lower() == "dxf":
        output = sys.argv[4] if len(sys.argv) > 4 else "output.dxf"
        cmd_export_dxf(skill_name, output)

    else:
        print(f"Comando desconocido: '{command}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
