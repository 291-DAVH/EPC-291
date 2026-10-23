#!/usr/bin/env python3
"""Generate simulated projects for demos (default 20) into local/projects-demo/.

  python tools/dev/seed_demo.py [--count 20] [--out DIR]

The folder is separate from projects/ so demo data never mixes with real projects. Everything here is
fictitious. Requirements are written the way the analysis step produces them (see docs/USER_DATA_MODEL.md).
Requires: openpyxl, ezdxf (already in requirements.txt).
"""
import argparse
import datetime as dt
import json
import random
import shutil
from pathlib import Path

W = Path(__file__).resolve().parents[2]
TEMPLATE = W / "management" / "templates" / "project-skeleton"
TODAY = dt.date(2026, 10, 23)

CLIENTS = [
    ("Industrias Aurora S.A.", "AURORA"), ("Frigorífico Patagonia", "PATAGONIA"), ("Alimentos del Litoral", "LITORAL"),
    ("Metalúrgica Cuyo", "CUYO"), ("Laboratorios Andina", "ANDINA"), ("Hospital Regional Sur", "HRSUR"),
    ("Logística Pampa", "PAMPA"), ("Cerámica Norte", "NORTE"), ("Bodega Los Cóndores", "CONDORES"),
    ("Plásticos del Plata", "PLATA"), ("Centro Comercial Ágora", "AGORA"), ("Textil Rioplatense", "RIOPLATA"),
    ("Cooperativa Agroindustrial", "COOPAGRO"), ("Parque Solar Sierras", "SIERRAS"), ("Data Center Austral", "AUSTRAL"),
    ("Papelera San Martín", "SANMARTIN"), ("Puerto Seco Cuyano", "PUERTOSECO"), ("Universidad Tecnológica Regional", "UTR"),
    ("Química Delta", "DELTA"), ("Aeroclub Internacional", "AEROCLUB"),
]
PROJECTS = [
    "Ampliación de planta y nuevo tablero general", "Cámara frigorífica y sala de máquinas", "Línea de envasado automática",
    "Nave de mecanizado y puente grúa", "Sala limpia clase ISO 8", "Quirófanos y terapia intensiva", "Centro de distribución",
    "Horno túnel y subestación", "Planta de fraccionamiento", "Extrusión y reciclado", "Remodelación de cines y patio de comidas",
    "Planta de hilandería", "Silos y secadora de granos", "Parque solar de 5 MW y obra de interconexión", "Sala de servidores Tier III",
    "Máquina papelera y tratamiento de efluentes", "Playa de contenedores y iluminación", "Laboratorios y aulas de ingeniería",
    "Planta de ácido sulfúrico, modernización", "Hangar y balizamiento de pista",
]
MANAGERS = ["M. Ferreyra", "L. Quiroga", "A. Benítez", "C. Salvatierra", "P. Duarte", "J. Villalba", "R. Acosta", "S. Medina"]
CITIES = ["Córdoba", "Rosario", "Mendoza", "Neuquén", "Tucumán", "Bahía Blanca", "Salta", "Santa Fe", "San Juan", "Mar del Plata"]
DISC_NAME = {"electrical": "Eléctrica", "civil": "Civil", "hvac": "HVAC", "fire": "Incendio", "mechanical": "Mecánica",
             "instrumentation": "Instrumentación", "telecom": "Telecomunicaciones"}
CATALOG = {
    "electrical": [("Memoria de cálculo de baja tensión", "pdf"), ("Diagrama unifilar del tablero general", "dxf"), ("Planilla de cargas", "xlsx"),
                   ("Lista de cables", "xlsx"), ("Pliego técnico eléctrico", "pdf"), ("Plano de bandejas y canalizaciones", "dxf")],
    "civil": [("Memoria de cálculo estructural", "pdf"), ("Plano de fundaciones", "dxf"), ("Cómputo de materiales de obra civil", "xlsx"), ("Pliego técnico civil", "pdf")],
    "hvac": [("Memoria de cargas térmicas", "pdf"), ("Plano de conductos", "dxf"), ("Lista de equipos de climatización", "xlsx"), ("Pliego técnico de HVAC", "pdf")],
    "fire": [("Memoria hidráulica de rociadores", "pdf"), ("Plano de red contra incendio", "dxf"), ("Lista de materiales contra incendio", "xlsx"), ("Pliego de detección y alarma", "pdf")],
    "mechanical": [("Memoria de equipos mecánicos", "pdf"), ("Plano de disposición de equipos", "dxf"), ("Lista de equipos mecánicos", "xlsx")],
    "instrumentation": [("Lista de instrumentos", "xlsx"), ("Diagrama de lazos de control", "dxf"), ("Memoria de filosofía de control", "pdf")],
    "telecom": [("Plano de cableado estructurado", "dxf"), ("Memoria de red de datos", "pdf"), ("Lista de puntos de red", "xlsx")],
}

# (kind, title, text, discipline, requirement)  ->  requirement = (statement, type, priority, acceptance, open_questions)
VOC = [
    ("voice_of_customer", "Continuidad de la línea", "Si se corta la luz no podemos parar la línea de producción más de 10 segundos, nos cuesta muchísimo.", "electrical",
     ("Las cargas críticas de producción se mantienen alimentadas ante un corte de red, con una interrupción de hasta 10 segundos.", "no funcional", "alta",
      ["Ensayo de transferencia automática con interrupción menor o igual a 10 s", "Lista de cargas críticas aprobada por el cliente"], ["¿Cuáles son las cargas críticas y su potencia total?"])),
    ("user_story", "Operador y tableros", "Como operador quiero ver desde el tablero cuál circuito se disparó para volver a producir rápido.", "electrical",
     ("Cada circuito del tablero principal tiene identificación visible y señalización del estado de la protección.", "funcional", "media",
      ["Rótulo legible en cada salida", "Señalización de disparo en los circuitos críticos"], [])),
    ("voice_of_customer", "Crecimiento futuro", "Vamos a duplicar la producción en tres años, no quiero rehacer todo la próxima vez.", "electrical",
     ("La instalación eléctrica prevé una reserva de capacidad y espacio para la ampliación futura.", "restricción", "media",
      ["Reserva de espacio en tableros y bandejas definida en el pliego", "Capacidad de reserva indicada en la memoria"], ["¿Qué porcentaje de crecimiento se debe prever?"])),
    ("meeting_note", "Reunión de arranque", "Reunión del lunes: el cliente exige que los planos se entreguen en formato editable y con su rótulo corporativo.", "general",
     ("Los planos se entregan en formato editable (DXF) con el rótulo corporativo del cliente.", "documental", "alta",
      ["Planos en DXF con rótulo del cliente", "Logo y datos del cliente cargados antes de la primera entrega"], ["¿Versión de AutoCAD que usa el cliente?"])),
    ("voice_of_customer", "Seguridad del personal", "Hemos tenido sustos con gente que toca cosas que no debe, queremos que quede todo protegido.", "electrical",
     ("La instalación incluye protección de las personas contra contactos eléctricos, con verificación documentada.", "no funcional", "alta",
      ["Memoria de protección contra choques eléctricos", "Protocolo de ensayo de la puesta a tierra"], ["¿Hay zonas húmedas o con agua en la planta?"])),
    ("user_story", "Reportes de consumo", "Como gerente de planta quiero un resumen mensual del consumo por sector para controlar costos.", "electrical",
     ("El sistema de medición entrega el consumo eléctrico por sector, con un resumen mensual.", "funcional", "media",
      ["Puntos de medición definidos por sector", "Formato del resumen mensual acordado"], ["¿Qué sectores se miden por separado?", "¿Se integra al sistema de gestión existente?"])),
    ("voice_of_customer", "Temperatura en proceso", "En verano la sala se pone insoportable y los equipos se recalientan, es un problema de todos los años.", "hvac",
     ("La sala mantiene la temperatura de diseño en verano para el funcionamiento de los equipos.", "no funcional", "alta",
      ["Memoria de cargas térmicas con condición de verano", "Ensayo de temperatura en la puesta en marcha"], ["¿Cuál es la temperatura máxima admitida por los equipos?"])),
    ("user_story", "Ruido", "Como vecino del sector administrativo no quiero ruido de equipos de aire en horario de oficina.", "hvac",
     ("Los equipos de climatización cercanos a oficinas cumplen un nivel de ruido acordado.", "no funcional", "baja",
      ["Nivel sonoro máximo indicado en la especificación de equipos"], ["¿Qué nivel de ruido se considera aceptable?"])),
    ("meeting_note", "Seguro de incendio", "La aseguradora pide cumplir su norma de rociadores para renovar la póliza antes de marzo.", "fire",
     ("El sistema contra incendio cumple la norma exigida por la aseguradora, con plazo de aprobación anterior a marzo.", "restricción", "alta",
      ["Aprobación escrita de la aseguradora sobre el diseño", "Memoria hidráulica entregada antes de la fecha límite"], ["¿Qué norma de la aseguradora aplica exactamente?"])),
    ("voice_of_customer", "Evacuación", "Si hay fuego la gente tiene que salir rápido y sin confusión, hubo un simulacro y fue un desastre.", "fire",
     ("El proyecto contempla señalización y alarma de evacuación visibles desde todos los puestos de trabajo.", "funcional", "alta",
      ["Plano de ubicación de pulsadores y sirenas", "Ensayo de audibilidad y visibilidad"], [])),
    ("user_story", "Piso del depósito", "Como jefe de logística quiero que el piso aguante autoelevadores cargados sin romperse como el anterior.", "civil",
     ("El piso del depósito soporta el tránsito de autoelevadores con la carga máxima definida.", "no funcional", "alta",
      ["Memoria de cálculo del pavimento con la carga de diseño", "Ensayo de resistencia del hormigón"], ["¿Peso máximo de los autoelevadores y de la carga?"])),
    ("voice_of_customer", "Plazos de obra", "No podemos parar el depósito más de dos fines de semana, la obra tiene que ser por etapas.", "civil",
     ("La ejecución se planifica por etapas, de modo que el depósito no pare más de dos fines de semana.", "restricción", "alta",
      ["Plan por etapas aprobado por el cliente", "Ventanas de intervención acordadas"], ["¿Qué fechas son aceptables para cada ventana?"])),
    ("meeting_note", "Compresores", "El cliente quiere que los compresores queden accesibles para mantenimiento con autoelevador.", "mechanical",
     ("La disposición de los equipos mecánicos permite el acceso para mantenimiento con equipos de elevación.", "funcional", "media",
      ["Plano de disposición con pasillos y radios de giro", "Verificación de espacios libres de mantenimiento"], [])),
    ("user_story", "Mantenimiento", "Como mantenedor quiero lista de repuestos críticos con proveedores locales para no depender de importaciones.", "mechanical",
     ("Se entrega una lista de repuestos críticos con proveedores locales y plazos de entrega.", "documental", "media",
      ["Lista de repuestos críticos con proveedor y plazo", "Aprobación del área de mantenimiento"], ["¿Cuántos meses de repuestos se desea tener en stock?"])),
    ("voice_of_customer", "Control de proceso", "Queremos ver en una pantalla todas las temperaturas y alarmas, y que nos avise al celular si algo se va de rango.", "instrumentation",
     ("El sistema de control muestra las variables de proceso y envía alarmas a dispositivos móviles cuando salen de rango.", "funcional", "alta",
      ["Lista de variables y rangos de alarma aprobada", "Prueba de envío de alarmas al celular"], ["¿Qué variables son críticas?", "¿Quiénes reciben las alarmas?"])),
    ("meeting_note", "Calibración", "Los instrumentos deben tener certificado de calibración trazable antes de la puesta en marcha.", "instrumentation",
     ("Todos los instrumentos críticos se entregan con certificado de calibración trazable.", "documental", "media",
      ["Certificados de calibración archivados por instrumento"], [])),
    ("voice_of_customer", "Internet en planta", "Hoy el wifi no llega al fondo del galpón y los scanners se desconectan todo el tiempo.", "telecom",
     ("La red inalámbrica cubre toda la superficie del galpón con conectividad estable para los lectores.", "no funcional", "alta",
      ["Estudio de cobertura inalámbrica", "Prueba de movimiento de lectores en todo el galpón"], ["¿Cuántos lectores simultáneos se esperan?"])),
    ("user_story", "Cámaras", "Como responsable de seguridad quiero ver las cámaras de portería desde mi oficina y desde casa.", "telecom",
     ("Las cámaras de portería se pueden ver de forma remota desde la oficina y desde fuera de la planta.", "funcional", "baja",
      ["Acceso remoto verificado con usuario autorizado"], ["¿Se permite el acceso desde internet según la política de seguridad?"])),
    ("voice_of_customer", "Costos", "El presupuesto está muy ajustado, necesitamos saber qué se puede dejar para una segunda etapa.", "general",
     ("Se identifican los alcances que pueden diferirse a una segunda etapa sin afectar la operación.", "restricción", "media",
      ["Lista de alcances diferibles aprobada por el cliente"], ["¿Cuál es el hito de segunda etapa?"])),
    ("document", "Pliego del cliente", "Documento: especificaciones generales de la empresa para contratistas (versión 4).", "general",
     ("Se cumplen las especificaciones generales para contratistas del cliente, versión 4.", "documental", "alta",
      ["Lista de cumplimiento contra las especificaciones del cliente"], ["¿Hay requisitos adicionales de seguridad e higiene?"])),
    ("meeting_note", "Documentación final", "El cliente quiere recibir la documentación as-built en carpeta digital ordenada por sector.", "general",
     ("La documentación final se entrega en una carpeta digital organizada por sector.", "documental", "media",
      ["Índice de documentación por sector aprobado"], [])),
    ("user_story", "Acceso a datos", "Como administrador quiero descargar las planillas en Excel para trabajarlas con mis datos.", "general",
     ("Las planillas de datos se entregan en formato Excel editable.", "documental", "baja", ["Planillas en XLSX entregadas junto con los PDF"], [])),
]
REPORTS = [("Informe de avance semanal", "avance"), ("Informe de estado mensual", "estado"), ("Informe de riesgos", "riesgos"), ("Informe de coordinación", "coordinación")]


def pdf_bytes(title, lines):
    def esc(s):
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("latin-1", "replace").decode("latin-1")
    content = "BT /F1 16 Tf 56 780 Td (" + esc(title) + ") Tj /F1 10 Tf"
    for ln in lines:
        content += " 0 -18 Td (" + esc(ln) + ") Tj"
    content += " ET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            f"<< /Length {len(content)} >>\nstream\n{content}\nendstream"]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    x = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for o in offs:
        out += f"{o:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n".encode()
    return out


def write_file(path: Path, fmt: str, title: str, client: str, code: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "pdf":
        path.write_bytes(pdf_bytes(title, [f"Cliente: {client}", f"Proyecto: {code}", "Revisión: Rev 00", "Documento de demostración (datos simulados)."]))
    elif fmt == "xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Datos"
        ws.append([title])
        ws.append(["Cliente", client])
        ws.append(["Proyecto", code])
        ws.append([])
        ws.append(["Ítem", "Descripción", "Cantidad"])
        for i in range(1, 6):
            ws.append([i, f"Elemento {i} (simulado)", i * 3])
        wb.save(path)
    elif fmt == "dxf":
        import ezdxf
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        msp.add_lwpolyline([(0, 0), (420, 0), (420, 297), (0, 297)], close=True)
        msp.add_text(title, dxfattribs={"height": 8}).set_placement((20, 270))
        msp.add_text(f"{client} - {code} - Rev 00", dxfattribs={"height": 5}).set_placement((20, 255))
        doc.saveas(path)


def jdump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


BACKLOG_POOL = [
    ("Verificar niveles de cortocircuito con datos de la distribuidora", "task", "P1", 6), ("Consultar al cliente por el sistema de respaldo (UPS)", "question", "P2", 1),
    ("Cambio de ubicación del tablero general solicitado en reunión", "change", "P1", 10), ("Riesgo: demora en la entrega de transformadores", "risk", "P1", 2),
    ("Actualizar la planilla de cargas con las cargas nuevas", "task", "P2", 4), ("Revisar la selectividad de protecciones", "task", "P2", 8),
    ("Observación del revisor: falta rótulo en el plano de bandejas", "defect", "P3", 1), ("Definir criterio de aceptación del ensayo de transferencia", "question", "P2", 2),
    ("Preparar la lista de repuestos críticos", "task", "P3", 5), ("Coordinar interferencias con civil e incendio", "task", "P2", 6),
]


def planning(i, ws, discs, start, due, progress, rnd):
    """WBS (progress spread in order of work), schedule and backlog, consistent with the project progress."""
    kinds = [("Memorias de cálculo", 3), ("Planos y diagramas", 4), ("Listas y planillas", 2)]
    nodes = [{"id": "1", "name": "Gestión del proyecto"}, {"id": "1.1", "name": "Plan de gestión y seguimiento", "weight": 1},
             {"id": "1.2", "name": "Informes de avance", "weight": 1}, {"id": "2", "name": "Ingeniería"}]
    for k, d in enumerate(discs, 1):
        nodes.append({"id": f"2.{k}", "name": DISC_NAME[d], "discipline": d})
        for m, (nm, w) in enumerate(kinds, 1):
            nodes.append({"id": f"2.{k}.{m}", "name": f"{nm} - {DISC_NAME[d]}", "discipline": d, "weight": w})
    nodes += [{"id": "3", "name": "Cierre"}, {"id": "3.1", "name": "Documentación final y conforme a obra", "weight": 2}]
    leaves = [n for n in nodes if not any(o["id"].startswith(n["id"] + ".") for o in nodes)]
    remaining = progress / 100.0 * sum(n["weight"] for n in leaves)
    for n in leaves:
        pr = max(0.0, min(1.0, remaining / n["weight"]))
        n["progress"] = round(pr * 100, 1)
        remaining -= pr * n["weight"]
    for n in nodes:
        n.setdefault("weight", 1)
        n.setdefault("progress", 0)
        n.setdefault("discipline", "")
        n["deliverable_id"] = ""
        n["owner"] = ""
    jdump(ws / "05-management" / "wbs.json", {"schema_version": "1.0", "nodes": nodes})

    span = max((due - start).days, 60)
    plan = [("A1", "Arranque del proyecto", 0.0, 0.0, [], "1.1", True), ("A2", "Ingeniería básica", 0.0, 0.3, ["A1"], "2", False),
            ("A3", "Ingeniería de detalle", 0.3, 0.65, ["A2"], "2", False), ("A4", "Revisión y emisión", 0.65, 0.9, ["A3"], "2", False),
            ("A5", "Documentación final", 0.9, 0.99, ["A4"], "3", False), ("A6", "Entrega final", 1.0, 1.0, ["A5"], "3", True)]
    acts = []
    for aid, name, f0, f1, dep, wbs, ms in plan:
        s = start + dt.timedelta(days=int(span * f0) + (0 if not dep else 1))
        e = s if ms else start + dt.timedelta(days=int(span * f1))
        e = max(e, s)
        pr = 100 if ms and progress >= f0 * 100 else max(0, min(100, round((progress / 100 - f0) / (f1 - f0) * 100))) if f1 > f0 else 0
        acts.append({"id": aid, "name": name, "start": s.isoformat(), "end": e.isoformat(), "wbs_id": wbs, "depends_on": dep, "milestone": ms, "progress": pr})
    jdump(ws / "05-management" / "schedule.json", {"schema_version": "1.0", "activities": acts})

    items = []
    for q, (title, typ, prio, est) in enumerate(rnd.sample(BACKLOG_POOL, rnd.randint(3, 7)), 1):
        items.append({"id": f"BL-{q:03d}", "title": title, "type": typ, "priority": prio, "status": rnd.choice(["backlog", "todo", "todo", "doing", "done"]),
                      "estimate_h": est, "wbs_id": "", "requirement_id": "", "owner": "", "created": (TODAY - dt.timedelta(days=rnd.randint(1, 60))).isoformat()})
    jdump(ws / "05-management" / "backlog.json", {"schema_version": "1.0", "items": items})


def sld_svg(project, feeders, three_line=False):
    """Small illustrative single-line (or multi-line) diagram of a main board with its feeders. Simulated data."""
    w = 160 + 120 * len(feeders)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 330" width="{w}" height="330" font-family="Arial" font-size="11">',
           '<rect width="100%" height="100%" fill="#fff"/>',
           f'<text x="12" y="20" font-size="13" font-weight="bold">{project} - Tablero general ({"multifilar" if three_line else "unifilar"})</text>']
    mid = [w / 2 + (k - 1) * 8 for k in range(3)] if three_line else [w / 2]
    for x in mid:
        out.append(f'<line x1="{x}" y1="40" x2="{x}" y2="95" stroke="#000" stroke-width="1.5"/>')
        out.append(f'<rect x="{x - 9}" y="95" width="18" height="26" fill="#fff" stroke="#000" stroke-width="1.5"/>')
        out.append(f'<line x1="{x}" y1="121" x2="{x}" y2="150" stroke="#000" stroke-width="1.5"/>')
    out.append(f'<text x="{w / 2 + 28}" y="62">Red BT 3x380/220 V</text><text x="{w / 2 + 28}" y="112">Interruptor general</text>')
    out.append(f'<line x1="70" y1="150" x2="{w - 70}" y2="150" stroke="#000" stroke-width="5"/><text x="70" y="143">Barra principal</text>')
    for i, (name, amps) in enumerate(feeders):
        x = 100 + 120 * i
        xs = [x - 8, x, x + 8] if three_line else [x]
        for xx in xs:
            out.append(f'<line x1="{xx}" y1="150" x2="{xx}" y2="190" stroke="#000" stroke-width="1.5"/>')
            out.append(f'<rect x="{xx - 6}" y="190" width="12" height="20" fill="#fff" stroke="#000" stroke-width="1.5"/>')
            out.append(f'<line x1="{xx}" y1="210" x2="{xx}" y2="255" stroke="#000" stroke-width="1.5"/>')
        out.append(f'<circle cx="{x}" cy="270" r="14" fill="#fff" stroke="#000" stroke-width="1.5"/><text x="{x - 4}" y="274">M</text>')
        out.append(f'<text x="{x - 38}" y="305">{name}</text><text x="{x - 38}" y="319">{amps} A</text>')
    out.append("</svg>")
    return "\n".join(out)


def engineering(pdir, ccode, code, discs, rnd):
    """Engineering workspace content: SVG diagrams and text lists (what the engineer sees in the Engineering tab)."""
    base = pdir / "workspace" / "02-engineering"
    feeders = [(rnd.choice(["Fuerza motriz", "Iluminación", "Tomas", "Climatización", "Bombas", "Compresor", "Tablero seccional"]), rnd.choice([16, 25, 32, 40, 63, 100])) for _ in range(rnd.randint(3, 5))]
    el = base / "electrical" / "PQ-01"
    (el / "drawings" / "svg").mkdir(parents=True, exist_ok=True)
    (el / "calc").mkdir(parents=True, exist_ok=True)
    (el / "docs").mkdir(parents=True, exist_ok=True)
    (el / "drawings" / "svg" / "SLD-tablero-general.svg").write_text(sld_svg(code, feeders), encoding="utf-8", newline="\n")
    (el / "drawings" / "svg" / "MLD-tablero-general.svg").write_text(sld_svg(code, feeders, True), encoding="utf-8", newline="\n")
    rows = ["circuito;descripcion;potencia_kW;corriente_A;seccion_mm2;caida_pct"]
    for k, (name, amps) in enumerate(feeders, 1):
        sec = {16: 2.5, 25: 4, 32: 6, 40: 10, 63: 16, 100: 35}[amps]
        rows.append(f"C{k:02d};{name};{round(amps * 0.38 * 1.73 * 0.85, 1)};{amps};{sec};{round(rnd.uniform(0.6, 2.8), 1)}")
    (el / "calc" / "cuadro-de-cargas.csv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    (el / "calc" / "lista-de-cables.csv").write_text("cable;origen;destino;longitud_m\n" + "\n".join(
        f"CB-{k:02d};Tablero general;{n};{rnd.randint(8, 90)}" for k, (n, _) in enumerate(feeders, 1)) + "\n", encoding="utf-8", newline="\n")
    for d in discs:
        if d == "electrical":
            continue
        pq = base / d / "PQ-01"
        (pq / "docs").mkdir(parents=True, exist_ok=True)
        (pq / "docs" / "alcance.md").write_text(f"# {DISC_NAME[d]} - alcance\n\nLista de documentos y criterios de la disciplina (datos simulados).\n", encoding="utf-8", newline="\n")


def build_project(i, root, rnd):
    client, ccode = CLIENTS[i]
    pname = PROJECTS[i]
    code = f"{ccode[:4]}-{2026 if i % 4 else 2025}-{i + 1:03d}"
    discs = ["electrical"] + rnd.sample([d for d in DISC_NAME if d != "electrical"], rnd.choice([0, 1, 1, 2, 3]))
    phase = rnd.choice(["IC", "IB", "ID", "ID", "IE"])
    health = rnd.choices(["on_track", "at_risk", "delayed"], [58, 27, 15])[0]
    closed = i in (17, 19)
    progress = 100 if closed else {"IC": rnd.randint(5, 25), "IB": rnd.randint(25, 45), "ID": rnd.randint(45, 80), "IE": rnd.randint(80, 97)}[phase]
    if closed:
        phase, health = "ASB", "on_track"
    start = TODAY - dt.timedelta(days=rnd.randint(60, 380))
    due = TODAY + dt.timedelta(days=rnd.randint(-20, 200)) if not closed else TODAY - dt.timedelta(days=rnd.randint(10, 90))
    if health == "delayed" and due > TODAY:
        due = TODAY - dt.timedelta(days=rnd.randint(3, 25))
    pdir = root / ccode / code
    shutil.copytree(TEMPLATE, pdir, ignore=shutil.ignore_patterns("plugins.lock", "project.json"))
    ws = pdir / "workspace"
    meta = {"schema_version": "1.0", "client": client, "client_code": ccode, "project_code": code, "project_name": pname, "jurisdiction": "AR",
            "locale": "es-AR", "methodology": rnd.choice(["pm2", "pm2", "pm2", "pmi"]), "disciplines": discs, "phase": phase, "engine_min_version": "0.1.0",
            "created": start.isoformat() + "T09:00:00", "simulated": True}
    jdump(pdir / ".epc" / "project.json", meta)

    # deliverables
    items = []
    n = 0
    for d in discs:
        for name, fmt in CATALOG[d]:
            n += 1
            items.append({"id": f"ENT-{n:03d}", "code": f"{code}-{d[:3].upper()}-{n:03d}", "name": name, "discipline": d, "format": fmt, "revision": "Rev 00"})
    rnd.shuffle(items)
    items.sort(key=lambda x: x["id"])
    k = len(items)
    done = k if closed else int(k * max(0.0, (progress - 8) / 100.0))
    manager = rnd.choice(MANAGERS)
    for j, it in enumerate(items):
        if j < done:
            when = start + dt.timedelta(days=int((TODAY - start).days * (j + 1) / (done + 1)))
            it.update(status="delivered", delivered_on=when.isoformat(), due=when.isoformat())
            rel = f"ifa/TR-001_Rev00/{it['discipline']}/{it['code']}.{it['format']}"
            write_file(pdir / "deliverables" / rel, it["format"], it["name"], client, code)
            it["file"] = rel
        elif j == done and not closed:
            it.update(status="in_review", due=(TODAY + dt.timedelta(days=rnd.randint(2, 12))).isoformat())
        elif j < done + 3 and not closed:
            it.update(status="in_progress", due=(TODAY + dt.timedelta(days=rnd.randint(8, 50)) if health != "delayed" else TODAY - dt.timedelta(days=rnd.randint(2, 15))).isoformat())
        else:
            it.update(status="planned", due=(TODAY + dt.timedelta(days=rnd.randint(30, 160))).isoformat())
    jdump(ws / "05-management" / "deliverables.json", items)

    # milestones
    thresholds = [1, 30, 65, 100]
    ms = [("Arranque del proyecto", start), ("Ingeniería básica aprobada", start + (due - start) * 0.3),
          ("Ingeniería de detalle emitida", start + (due - start) * 0.65), ("Entrega final", due)]
    miles = []
    for (nme, d), thr in zip(ms, thresholds):
        d = d if isinstance(d, dt.date) and not isinstance(d, dt.datetime) else d.date()
        miles.append({"name": nme, "date": d.isoformat(), "done": progress >= thr})
    nxt = next((m for m in miles if not m["done"]), None)
    jdump(ws / "05-management" / "project-status.json", {
        "schema_version": "1.0", "state": "closed" if closed else "active", "progress_pct": progress, "health": health, "phase": phase,
        "manager": manager, "location": rnd.choice(CITIES), "start": start.isoformat(), "due": due.isoformat(),
        "next_milestone": nxt, "milestones": miles, "updated": (TODAY - dt.timedelta(days=rnd.randint(0, 6))).isoformat()})

    # intake + structured requirements
    pool = [v for v in VOC if v[3] in discs or v[3] == "general"]
    rnd.shuffle(pool)
    pick = pool[: rnd.randint(5, min(9, len(pool)))]
    reqs, nreq = [], 0
    for q, v in enumerate(pick, 1):
        kind, title, text, disc, req = v
        created = TODAY - dt.timedelta(days=rnd.randint(1, 120))
        status = rnd.choices(["structured", "analyzing", "received"], [62, 18, 20])[0]
        if (TODAY - created).days > 60 and status == "received":
            status = "structured"
        if closed:
            status = "structured"
        iid = f"INT-{q:04d}"
        rec = {"id": iid, "kind": kind, "title": title, "text": text, "source": rnd.choice(["Reunión con el cliente", "Correo del cliente", "Formulario web", "Llamada telefónica", "Visita a planta"]),
               "author": rnd.choice(["Gerencia de operaciones", "Jefe de mantenimiento", "Responsable de calidad", "Dirección técnica", manager]),
               "created": created.isoformat(), "status": status, "attachments": []}
        jdump(ws / "01-input" / "intake" / f"{iid}.json", rec)
        if status == "structured":
            nreq += 1
            statement, rtype, prio, acc, oq = req
            reqs.append({"id": f"REQ-{nreq:03d}", "statement": statement, "type": rtype, "priority": prio, "discipline": disc,
                         "acceptance": acc, "open_questions": oq, "source_intake": [iid], "status": "abierto" if oq else "definido"})
    jdump(ws / "00-setup" / "requirements.json", reqs)

    planning(i, ws, discs, start, due, progress, rnd)
    engineering(pdir, ccode, code, discs, rnd)

    # reports
    reps = []
    for r in range(rnd.randint(2, 4)):
        title, rtype = rnd.choice(REPORTS)
        d = TODAY - dt.timedelta(days=7 * (r + 1) + rnd.randint(0, 3))
        rid = f"INF-{r + 1:03d}"
        rel = f"informes/{rid}.pdf"
        write_file(pdir / "deliverables" / rel, "pdf", f"{title} - {d.isoformat()}", client, code)
        reps.append({"id": rid, "title": title, "type": rtype, "date": d.isoformat(), "file": rel,
                     "summary": f"Avance general {max(0, progress - 4 * (r + 1))}%. " + rnd.choice(
                         ["Sin desvíos relevantes en el período.", "Se detectó un retraso menor en la coordinación de planos.", "Pendiente respuesta del cliente sobre datos de entrada.", "Se emitieron los entregables previstos del período."])})
    jdump(ws / "05-management" / "reports" / "index.json", reps)
    return code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--out", default=str(W / "local" / "projects-demo"))
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        if out.name != "projects-demo":
            raise SystemExit("refusing to overwrite a folder that is not named projects-demo")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    rnd = random.Random(2026)
    for i in range(min(a.count, len(CLIENTS))):
        print(build_project(i, out, rnd))
    print(f"{min(a.count, len(CLIENTS))} simulated projects in {out}")


if __name__ == "__main__":
    main()
